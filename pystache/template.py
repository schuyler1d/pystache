import re
import cgi
import collections

modifiers = {}
def modifier(symbol):
    """Decorator for associating a function with a Mustache tag modifier.

    @modifier('P')
    def render_tongue(self, tag_name=None, context=None):
        return ":P %s" % tag_name

    {{P yo }} => :P yo
    """
    def set_modifier(func):
        modifiers[symbol] = func
        return func
    return set_modifier


def get_or_attr_dot_separator(obj, name, default=None):
    refs = name.split('.')
    if len(refs)==1:
        return get_or_attr(obj,name,default)
    else:
        for ref in refs:
            obj = get_or_attr(obj,ref)
            if obj is None:
                return default
        return obj

_get_tries = [
    (lambda o,n:o[n], KeyError),
    (lambda o,n:o[int(n)], (IndexError,ValueError,) ),
    (lambda o,n:getattr(o,n), AttributeError),
]

def get_or_attr(obj, name, default=None):
    for _try in _get_tries:
        try:
            return _try[0](obj,name)
        except _try[1]:
            return default
        except:
            continue
    return default


class Template(object):
    # The regular expression used to find a #section
    section_re = None

    # The regular expression used to find a tag.
    tag_re = None

    # Opening tag delimiter
    otag = '{{'

    # Closing tag delimiter
    ctag = '}}'

    def __init__(self, template, context=None):
        self.template = template
        self.context = context or {}
        self.compile_regexps()
        self.get_sub = get_or_attr
        if getattr(context,'template_dots',False):
            self.get_sub = get_or_attr_dot_separator

    def render(self, template=None, context=None, encoding=None):
        """Turns a Mustache template into something wonderful."""
        template = template or self.template
        context = context or self.context

        template = self.render_sections(template, context)
        result = self.render_tags(template, context)
        if encoding is not None:
            result = result.encode(encoding)
        return result

    def compile_regexps(self):
        """Compiles our section and tag regular expressions."""
        tags = { 'otag': re.escape(self.otag), 'ctag': re.escape(self.ctag) }

        section = r"(\n?)([ \t]*)%(otag)s([\#|^])([^\}]*)%(ctag)s\s*(.+?)[ \t]*%(otag)s/\4%(ctag)s([ \t]*)(\n?)"
        self.section_re = re.compile(section % tags, re.M|re.S)

        tag = r"%(otag)s(#|=|&|!|>|\{)?(.+?)\1?%(ctag)s+"
        self.tag_re = re.compile(tag % tags)

    def render_sections(self, template, context):
        """Expands sections."""
        while 1:
            match = self.section_re.search(template)
            if match is None:
                break

            section, newline, indent, section_type, section_name, inner, \
                trailing_space, trailing_nl = match.group(0, 1, 2, 3, 4, 5, 6, 7)
            section_name = section_name.strip()

            join = lambda *args, **kwargs: \
                    kwargs.get('delimiter', '').join([arg for arg in args])

            if trailing_nl:
                trailing_space = ''
            if inner.endswith("\n"):
                trailing_nl = ''

            inner = join(indent, inner, trailing_space, trailing_nl)
            it = self.get_sub(context, section_name, None)
            replacer = ''
            # Callable section
            if it and isinstance(it, collections.Callable):
                replacer = it(inner)
            # Inverted section with a non-false value
            elif it and section_type == '^':
                replacer = join(trailing_space, trailing_nl)
            # Pure-text section
            elif it and not hasattr(it, '__iter__'):
                replacer = inner
            # Section with context
            elif it and hasattr(it, 'keys') and hasattr(it, '__getitem__'):
                new_context = context.copy()
                new_context.update(it)
                replacer = self.render(inner, new_context)
            # Looping section
            elif it:
                insides = []
                for item in it:
                    new_context = context.copy()
                    new_context.update(item)
                    insides.append(self.render(inner, new_context))
                replacer = ''.join(insides)
            # Inverted section
            elif not it and section_type == '^':
                replacer = inner
            # Section with false value
            else:
                replacer = join(indent, trailing_space, trailing_nl)

            template = template.replace(section, join(newline, replacer))

        return template

    def render_tags(self, template, context):
        """Renders all the tags in a template for a context."""
        while 1:
            match = self.tag_re.search(template)
            if match is None:
                break

            tag, tag_type, tag_name = match.group(0, 1, 2)
            tag_name = tag_name.strip()
            func = modifiers[tag_type]
            replacement = func(self, tag_name, context)
            template = template.replace(tag, replacement)

        return template

    @modifier(None)
    def render_tag(self, tag_name, context):
        """Given a tag name and context, finds, escapes, and renders the tag."""
        raw = self.get_sub(context, tag_name, '')
        if not raw and raw is not 0:
            return ''
        return cgi.escape(unicode(raw))

    @modifier('!')
    def render_comment(self, tag_name=None, context=None):
        """Rendering a comment always returns nothing."""
        return ''

    @modifier('{')
    @modifier('&')
    def render_unescaped(self, tag_name=None, context=None):
        """Render a tag without escaping it."""
        return unicode(self.get_sub(context, tag_name, ''))

    @modifier('>')
    def render_partial(self, tag_name=None, context=None):
        """Renders a partial within the current context."""
        # Import view here to avoid import loop
        from pystache.view import View

        view = View(context=context)
        view.template_name = tag_name

        return view.render()

    @modifier('=')
    def render_delimiter(self, tag_name=None, context=None):
        """Changes the Mustache delimiter."""
        self.otag, self.ctag = tag_name.split(' ')
        self.compile_regexps()
        return ''
