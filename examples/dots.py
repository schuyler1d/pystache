import pystache

class Dots(pystache.View):
    template_path = 'examples'
    template_dots = True

    def outer_thing(self):
        return "two"

    def foo(self):
        return {'thing1': 'one', 'thing2': ['zero','four','three']}
