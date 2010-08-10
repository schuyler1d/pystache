# encoding: utf-8

import unittest
import pystache

class TestPystache(unittest.TestCase):
    def test_basic(self):
        ret = pystache.render("Hi {{thing}}!", { 'thing': 'world' })
        self.assertEquals(ret, "Hi world!")

    def test_kwargs(self):
        ret = pystache.render("Hi {{thing}}!", thing='world')
        self.assertEquals(ret, "Hi world!")

    def test_less_basic(self):
        template = "It's a nice day for {{beverage}}, right {{person}}?"
        ret = pystache.render(template, { 'beverage': 'soda', 'person': 'Bob' })
        self.assertEquals(ret, "It's a nice day for soda, right Bob?")

    def test_even_less_basic(self):
        template = "I think {{name}} wants a {{thing}}, right {{name}}?"
        ret = pystache.render(template, { 'name': 'Jon', 'thing': 'racecar' })
        self.assertEquals(ret, "I think Jon wants a racecar, right Jon?")

    def test_ignores_misses(self):
        template = "I think {{name}} wants a {{thing}}, right {{name}}?"
        ret = pystache.render(template, { 'name': 'Jon' })
        self.assertEquals(ret, "I think Jon wants a , right Jon?")

    def test_render_zero(self):
        template = 'My value is {{value}}.'
        ret = pystache.render(template, { 'value': 0 })
        self.assertEquals(ret, 'My value is 0.')

    def test_comments(self):
        template = "What {{! the }} what?"
        ret = pystache.render(template)
        self.assertEquals(ret, "What  what?")

    def test_false_sections_are_hidden(self):
        template = "Ready {{#set}}set {{/set}}go!"
        ret = pystache.render(template, { 'set': False })
        self.assertEquals(ret, "Ready go!")

    def test_true_sections_are_shown(self):
        template = "Ready {{#set}}set{{/set}} go!"
        ret = pystache.render(template, { 'set': True })
        self.assertEquals(ret, "Ready set go!")

    def test_non_strings(self):
        template = "{{#stats}}({{key}} & {{value}}){{/stats}}"
        stats = []
        stats.append({'key': 123, 'value': ['something']})
        stats.append({'key': u"chris", 'value': 0.900})

        ret = pystache.render(template, { 'stats': stats })
        self.assertEquals(ret, """(123 & ['something'])(chris & 0.9)""")

    def test_unicode(self):
        template = 'Name: {{name}}; Age: {{age}}'
        ret = pystache.render(template, { 'name': u'Henri Poincaré',
            'age': 156 })
        self.assertEquals(ret, u'Name: Henri Poincaré; Age: 156')

    def test_sections(self):
        template = """
<ul>
  {{#users}}
    <li>{{name}}</li>
  {{/users}}
</ul>
"""

        context = { 'users': [ {'name': 'Chris'}, {'name': 'Tom'}, {'name': 'PJ'} ] }
        ret = pystache.render(template, context)
        self.assertEquals(ret, """
<ul>
  <li>Chris</li>
  <li>Tom</li>
  <li>PJ</li>
</ul>
""")

    def test_inner_context_not_propagates_variables(self):
        template = "{{#foo}}{{thing1}} and {{thing2}} and {{outer_thing}}{{/foo}}{{^foo}}Not foo!{{/foo}} {{thing2}}"
        context = {'outer_thing': 'two', 'foo': {'thing1': 'one', 'thing2': 'foo'}}

        class InnerContext(pystache.View):
            def outer_thing(self):
                return "two"
            def foo(self):
                return {'thing1': 'one', 'thing2': 'foo'}

        view = InnerContext(template=template)
        ret = pystache.render(template, context)
        self.assertEquals(ret, "one and foo and two ")
        self.assertEquals(view.render(), "one and foo and two ")

    def test_inner_context_looping(self):
        template = """Say '{{greeting}}', everyone:

        {{#list}}
          {{name}} says: {{greeting}}
        {{/list}}
        """
        context = {
        "greeting": "hello",
        "list": [
                    {"name": "eeny"},
                    {"name": "meeny"},
                    {"name": "miney"},
                    {"name": "mo"}
                ]
        }
        ret = pystache.render(template, context)
        expected = """Say 'hello', everyone:

        eeny says: hello
        meeny says: hello
        miney says: hello
        mo says: hello
        """
        self.assertEquals(ret, expected)

    def test_preserve_whitespace(self):
        template = """<ul>\n    {{#link}}\n        <li><a href="{{url}}">{{text}}</a></li>\n    {{/link}}\n</ul>"""
        context = {
            'link': [
                        {'text': 'github', 'url': 'http://github.com'},
                        {'text': 'mustache', 'url': 'http://mustache.github.com'},
                        {'text': 'cheat sheets', 'url': 'http://cheat.errtheblog.com'},
            ]
        }
        expected = """<ul>\n    <li><a href="http://github.com">github</a></li>
    <li><a href="http://mustache.github.com">mustache</a></li>
    <li><a href="http://cheat.errtheblog.com">cheat sheets</a></li>\n</ul>""".strip()
        ret = pystache.render(template, context)
        self.assertEquals(ret, expected)

    def test_preserve_whitespace_nested_contexts(self):
        template = """
{{#blogroll}}
    {{#list}}
        <ul>
            {{#link}}
                    <li><a href="{{url}}">{{text}}</a></li>
            {{/link}}
        </ul>
    {{/list}}
{{/blogroll}}
""".strip()
        context = {
            'blogroll': {
                'list': {
                    'link': [
                                {'text': 'github', 'url': 'http://github.com'},
                                {'text': 'mustache', 'url': 'http://mustache.github.com'},
                                {'text': 'cheat sheets', 'url': 'http://cheat.errtheblog.com'},
                    ]
                }
            }
        }
        expected = """<ul>
            <li><a href="http://github.com">github</a></li>
            <li><a href="http://mustache.github.com">mustache</a></li>
            <li><a href="http://cheat.errtheblog.com">cheat sheets</a></li>
        </ul>\n"""
        ret = pystache.render(template, context)
        self.assertEquals(ret, expected)

if __name__ == '__main__':
    unittest.main()
