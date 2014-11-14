
import pkgutil
import traceback

__all__ = [] # No modules should be accessed statically
__running = {}


def available():
    plugins = []
    for imp, module, is_pkg in pkgutil.iter_modules(['plugins']):
        plugins.append(module)
    return plugins


def start_enabled_plugins():
    from options import options
    from urls import urls
    for module in available():
        if module in options.enabled_plugins and module not in __running:
            plugin_name = module
            import_name = __name__+'.'+module
            try:
                plugin = getattr(__import__(import_name), module)
                plugin_name = plugin.NAME
                plugin_link = plugin.LINK
                plugin_urls = plugin.URLS
                urls += plugin_urls
                __running[module] = plugin
                plugin.start()
                print 'Started the {} plug-in.'.format(plugin_name)
            except Exception as e:
                print 'Failed to load the {} plug-in:'.format(plugin_name)
                traceback.print_exc()
                options.enabled_plugins.remove(module)

    for module, plugin in __running.copy().iteritems():
        if module not in options.enabled_plugins:
            plugin_name = plugin.NAME
            plugin_urls = plugin.URLS
            try:
                for url in plugin_urls:
                    if url in urls:
                        urls.remove(url)
                plugin.stop()
                del __running[module]
                print 'Stopped the {} plug-in.'.format(plugin_name)
            except Exception as e:
                print 'Failed to stop the {} plug-in:'.format(plugin_name)
                traceback.print_exc()


def running():
    return __running.keys()


def get(name):
    return __running[name]