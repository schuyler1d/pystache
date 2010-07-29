import pystache

class InnerContextBubbling(pystache.View):
    template_path = 'examples'

    def outer_thing(self):
        return "two"

    def foo(self):
        return {'thing1': 'one', 'thing2': 'foo'}
