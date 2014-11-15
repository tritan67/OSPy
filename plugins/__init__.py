
import pkgutil
import traceback
import re
from os import path

__all__ = [] # No modules should be accessed statically
__running = {}


def available():
    plugins = []
    for imp, module, is_pkg in pkgutil.iter_modules(['plugins']):
        plugins.append(module)
    return plugins

def plugin_name(plugin):
    '''Tries to find the name of the given plugin without importing it yet.'''
    filename = path.join(path.dirname(__file__), plugin + '.py')
    with open(filename) as fh:
        for line in fh:
            if 'NAME' in line:
                match = re.search('NAME\\s=\\s("|\')([^"\']+)("|\')', line)
                if match is not None:
                    return match.group(2)
    return plugin


def plugin_names():
    return {plugin: plugin_name(plugin) for plugin in available()}


def plugin_url(cls):
    from webpages import WebPage
    import inspect
    if cls is None:
        result = cls
    else:
        if inspect.isclass(cls) and issubclass(cls, WebPage):
            cls = cls.__module__ + '.' + cls.__name__

        parts = cls.split('.')
        if len(parts) >= 3:
            result = '/p/' + '/'.join(parts[1:])
        elif len(parts) >= 2:
            result = '/p/' + '/'.join(parts)
        else:
            result = '/p/' + cls

        if result.endswith('_page'):
            result = result[:-5]

        if result.endswith('_json'):
            result = result[:-5] + '.json'

    return result


def _get_urls(import_name, plugin):
    from webpages import WebPage
    import inspect

    result = []
    for element in dir(plugin):
        if inspect.isclass(getattr(plugin, element)) and issubclass(getattr(plugin, element), WebPage):
            if import_name == getattr(plugin, element).__module__:
                classname = import_name + '.' + element
                result.append(plugin_url(classname))
                result.append(classname)

    return result


def start_enabled_plugins():
    from options import options
    from urls import urls
    for module in available():
        if module in options.enabled_plugins and module not in __running:
            plugin_name = module
            import_name = __name__ + '.' + module
            try:
                plugin = getattr(__import__(import_name), module)
                plugin_name = plugin.NAME
                if plugin.LINK is not None and not (plugin.LINK.startswith(module) or plugin.LINK.startswith(__name__)):
                    plugin.LINK = module + '.' + plugin.LINK
                plugin_urls = _get_urls(import_name, plugin)
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
            import_name = __name__+'.'+module
            plugin_name = plugin.NAME
            plugin_urls = _get_urls(import_name, plugin)
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