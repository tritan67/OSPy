import pkgutil
import traceback
import re
import sys
from os import path
import types

import web

__running = {}


class PluginStaticMiddleware(web.httpserver.StaticMiddleware):
    """WSGI middleware for serving static plugin files.
    This ensures all URLs starting with /p/static/plugin_name are mapped correctly."""

    def __call__(self, environ, start_response):
        upath = environ.get('PATH_INFO', '')
        upath = self.normpath(upath)

        if upath.startswith('/p' + self.prefix):
            parts = upath.split('/')
            if len(parts) > 3:
                module = parts[3]
                environ["PATH_INFO"] = '/'.join(['plugins', module, 'static'] + parts[4:])
            return web.httpserver.StaticApp(environ, start_response)
        else:
            return self.app(environ, start_response)


class PluginOptions(dict):
    def __init__(self, plugin, defaults):
        super(PluginOptions, self).__init__(defaults.iteritems())
        self._defaults = defaults.copy()

        from ospy.options import options

        if plugin in options:
            for key, value in options[plugin].iteritems():
                if key in self:
                    value_type = type(value)
                    if value_type == unicode:
                        value_type = str
                    default_type = type(self[key])
                    if default_type == unicode:
                        default_type = str

                    if value_type == default_type:
                        self[key] = value

        self._plugin = plugin

    def __setitem__(self, key, value):
        try:
            super(PluginOptions, self).__setitem__(key, value)
            if hasattr(self, '_plugin'):
                from ospy.options import options

                options[self._plugin] = self.copy()
        except ValueError:  # No index available yet
            pass

    def web_update(self, qdict, skipped=None):
        for key in self.keys():
            try:
                if skipped is not None and key in skipped:
                    continue
                default_value = self._defaults[key]
                old_value = self[key]
                if isinstance(default_value, bool):
                    self[key] = True if qdict.get(key, 'off') == 'on' else False
                elif isinstance(default_value, int):
                    self[key] = int(qdict.get(key, old_value))
                elif isinstance(default_value, float):
                    self[key] = float(qdict.get(key, old_value))
                elif isinstance(default_value, str) or isinstance(old_value, unicode):
                    self[key] = qdict.get(key, old_value)
            except ValueError:
                raise web.badrequest('Invalid value for \'%s\': \'%s\'' % (key, qdict.get(key)))


def available():
    plugins = []
    for imp, module, is_pkg in pkgutil.iter_modules(['plugins']):
        _protect(module)
        if plugin_name(module) is not None:
            plugins.append(module)
    return plugins


def plugin_name(plugin):
    """Tries to find the name of the given plugin without importing it yet."""
    filename = path.join(path.dirname(__file__), plugin, '__init__.py')
    try:
        with open(filename) as fh:
            for line in fh:
                if 'NAME' in line:
                    match = re.search('NAME\\s=\\s("|\')([^"\']+)("|\')', line)
                    if match is not None:
                        return match.group(2)
    except Exception:
        pass
    return None


def plugin_names():
    return {plugin: (plugin_name(plugin)) for plugin in available() if plugin_name(plugin)}


def plugin_url(cls):
    from ospy.webpages import WebPage
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

        if result.endswith('_csv'):
            result = result[:-4] + '.csv'

    return result


def plugin_dir(module=None):
    my_dir = path.dirname(path.abspath(__file__))

    if module is not None:
        if module.startswith('plugins.'):
            module = module[8:]
    else:
        stack = traceback.extract_stack()
        module = ''
        for tb in reversed(stack):
            tb_dir = path.dirname(path.abspath(tb[0]))
            if 'plugins' in tb_dir and tb_dir != my_dir:
                module = path.basename(tb_dir)
                break

    return path.join(my_dir, module)


def plugin_data_dir(module=None):
    return path.join(plugin_dir(module), 'data')


def plugin_docs_dir(module=None):
    return path.join(plugin_dir(module), 'docs')


def _get_urls(import_name, plugin):
    from ospy.webpages import WebPage
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
    from ospy.options import options
    import logging
    from ospy.urls import urls

    for module in available():
        if module in options.enabled_plugins and module not in __running:
            plugin_n = module
            import_name = __name__ + '.' + module
            try:
                plugin = getattr(__import__(import_name), module)
                plugin_n = plugin.NAME
                plugin.start()
                __running[module] = plugin
                logging.info('Started the {} plug-in.'.format(plugin_n))

                if plugin.LINK is not None and not (plugin.LINK.startswith(module) or plugin.LINK.startswith(__name__)):
                    plugin.LINK = module + '.' + plugin.LINK
                plugin_urls = _get_urls(import_name, plugin)
                urls += plugin_urls

            except Exception:
                logging.info('Failed to load the {} plug-in:'.format(plugin_n))
                traceback.print_exc()
                options.enabled_plugins.remove(module)

    for module, plugin in __running.copy().iteritems():
        if module not in options.enabled_plugins:
            import_name = __name__ + '.' + module
            plugin_n = plugin.NAME
            plugin_urls = _get_urls(import_name, plugin)
            try:
                for url in plugin_urls:
                    if url in urls:
                        urls.remove(url)
                plugin.stop()
                del __running[module]
                logging.info('Stopped the {} plug-in.'.format(plugin_n))
            except Exception:
                logging.info('Failed to stop the {} plug-in:'.format(plugin_n))
                traceback.print_exc()


def running():
    return __running.keys()


def get(name):
    if name not in __running:
        raise Exception('The %s plug-in is not running.' % name)
    return __running[name]


# The following (cryptic) functionality ensures disabled plug-ins will not be loaded by other parts of the code.
# Only enabled plug-ins will be allowed to be imported.
class _PluginWrapper(types.ModuleType):
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def __getattr__(self, name):
        return getattr(get(self._wrapped), name)


def _protect(module):
    if __name__ not in sys.modules:
        import_name = __name__ + '.' + module
        sys.modules[import_name] = _PluginWrapper(module)
        setattr(sys.modules[__name__], module, _PluginWrapper(module))
