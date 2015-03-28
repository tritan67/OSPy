import pkgutil
import traceback
import re
import sys
from os import path
import types

__running = {}


################################################################################
# Plugin Options                                                               #
################################################################################
class PluginOptions(dict):
    def __init__(self, plugin, defaults):
        super(PluginOptions, self).__init__(defaults.iteritems())
        self._defaults = defaults.copy()

        from ospy.options import options

        my_dir = path.dirname(path.abspath(__file__))
        plugin = 'plugin_unknown'
        stack = traceback.extract_stack()
        for tb in reversed(stack):
            abspath = path.dirname(path.abspath(tb[0]))
            if abspath.startswith(my_dir) and abspath != path.abspath(__file__):
                parts = abspath[len(my_dir):].split(path.sep)
                while parts and not parts[0]:
                    del parts[0]
                if parts:
                    plugin = 'plugin_' + parts[0]
                    break

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
                import web
                raise web.badrequest('Invalid value for \'%s\': \'%s\'' % (key, qdict.get(key)))


################################################################################
# Plugin App                                                                   #
################################################################################
def get_app():
    import web
    class PluginApp(web.application):
        def handle(self):
            mapping = []
            for module in running():
                import_name = __name__ + '.' + module
                plugin = get(module)
                mapping += _get_urls(import_name, plugin)
            fn, args = self._match(mapping, web.ctx.path)
            return self._delegate(fn, self.fvars, args)

    return PluginApp(fvars=locals())


################################################################################
# Plugin directories                                                           #
################################################################################
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


################################################################################
# Plugin information + urls                                                    #
################################################################################
def available():
    plugins = []
    for imp, module, is_pkg in pkgutil.iter_modules(['plugins']):
        _protect(module)
        if plugin_name(module) is not None:
            plugins.append(module)
    return plugins


__name_cache = {}
def plugin_name(plugin):
    """Tries to find the name of the given plugin without importing it yet."""
    if plugin not in __name_cache:
        __name_cache[plugin] = None
        filename = path.join(path.dirname(__file__), plugin, '__init__.py')
        try:
            with open(filename) as fh:
                for line in fh:
                    if 'NAME' in line:
                        match = re.search('NAME\\s=\\s("|\')([^"\']+)("|\')', line)
                        if match is not None:
                            __name_cache[plugin] = match.group(2)
        except Exception:
            pass
    return __name_cache[plugin]


def plugin_names():
    return {plugin: (plugin_name(plugin)) for plugin in available() if plugin_name(plugin)}


def plugin_url(cls, prefix='/plugins/'):
    from ospy.webpages import WebPage
    import inspect

    if cls is None:
        result = cls
    else:
        if inspect.isclass(cls) and issubclass(cls, WebPage):
            cls = cls.__module__ + '.' + cls.__name__

        parts = cls.split('.')
        if len(parts) >= 3:
            result = prefix + '/'.join(parts[1:])
        elif len(parts) >= 2:
            result = prefix + '/'.join(parts)
        else:
            result = prefix + cls

        if result.endswith('_page'):
            result = result[:-5]

        if result.endswith('_json'):
            result = result[:-5] + '.json'

        if result.endswith('_csv'):
            result = result[:-4] + '.csv'

    return result


__urls_cache = {}
def _get_urls(import_name, plugin):
    if plugin not in __urls_cache:
        from ospy.webpages import WebPage
        import inspect

        result = []
        for element in dir(plugin):
            if inspect.isclass(getattr(plugin, element)) and issubclass(getattr(plugin, element), WebPage):
                if import_name == getattr(plugin, element).__module__:
                    classname = import_name + '.' + element
                    result.append((plugin_url(classname, '/'), classname))
        __urls_cache[plugin] = result

    return __urls_cache[plugin]


################################################################################
# Plugin start/stop                                                            #
################################################################################
def start_enabled_plugins():
    from ospy.helpers import mkdir_p
    from ospy.options import options
    import logging

    for module in available():
        if module in options.enabled_plugins and module not in __running:
            plugin_n = module
            import_name = __name__ + '.' + module
            try:
                plugin = getattr(__import__(import_name), module)
                plugin_n = plugin.NAME
                mkdir_p(plugin_data_dir(module))
                mkdir_p(plugin_docs_dir(module))

                plugin.start()
                __running[module] = plugin
                logging.info('Started the {} plug-in.'.format(plugin_n))

                if plugin.LINK is not None and not (plugin.LINK.startswith(module) or plugin.LINK.startswith(__name__)):
                    plugin.LINK = module + '.' + plugin.LINK

            except Exception:
                logging.info('Failed to load the {} plug-in:'.format(plugin_n))
                traceback.print_exc()
                options.enabled_plugins.remove(module)

    for module, plugin in __running.copy().iteritems():
        if module not in options.enabled_plugins:
            plugin_n = plugin.NAME
            try:
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
