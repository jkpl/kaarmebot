import venusian as v


def plugin_config(**settings):
    def decorator(wrapped):
        sets = settings.copy()

        def callback(scanner, name, ob):
            if sets.get('name') is None:
                sets['name'] = name
            scanner.add_plugin(ob, **sets)

        info = v.attach(wrapped, callback, category='plugins')
        if info.scope == 'class' and sets.get('attr') is None:
            sets['attr'] = wrapped.__name__
        return wrapped
    return decorator


class PluginManager(object):
    def __init__(self, dispatcher, plugin_configurer=None):
        self.plugins = {}
        self.dispatcher = dispatcher
        self.plugin_configurer = plugin_configurer
        self.scanner = v.Scanner(add_plugin=self.add_plugin)

    def add_plugin(self, handler, name, **settings):
        nid = settings.get('name', name)
        if self.plugin_configurer:
            self.plugins[nid] = self.plugin_configurer(handler, nid, settings)
        else:
            self.plugins[nid] = (handler, settings)

    def add_binding(self, predicate, name, routing_class=None, **moresettings):
        handler, settings, = self.plugins[name]
        settings.update(moresettings)
        if routing_class:
            settings['routing_class'] = routing_class
        self.dispatcher.add_binding(
            settings['routing_class'], predicate, handler)

    def scan(self, module):
        self.scanner.scan(module)
