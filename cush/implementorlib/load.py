from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

import importlib
import pkgutil
import cush.implementor
import itertools

def get_implementor_path(app_name='default'):
    """
    Description:
        get the path to the implementors top-level package for the application named
        <app_name>
    Input:
        app_name: the name of the CushApplication object which we are getting the
            top-level directory of implementor packages for

    Output:
        the OS filesystem path to the top-level implementor package for the specified
        application name
    """
    if app_name == 'default':
        return cush.implementor.__path__
    else:
        msg = "Only default application name for implementors supported ATM"
        raise ValueError(msg)


def load_implementors(path=None, app_name='default', prefix='cush.implementor'):
    """
    Description:
        import all the available modules for the named application

    Input:
        path: optional list of directories to start searching in
            defaults to toplevel of the implementors for the cush application named
            <app_name>

        app_name: name of the cush application namespace to load; defaults to "default"
            if no path is given, this is used to find the path by name
            if path is given, this can force the loading of a given implementor
            package under a different name than the one specified by the filesystem

        prefix: what name prefix is given to the module object
    """
    log = LoggerAdapter(logger, {'name_ext' : 'load_implementors'})
    if path is None:
        path = get_implementor_path(app_name)

    if prefix[-1] != '.':
        prefix += '.'

    all_module_infos = list(pkgutil.walk_packages(path=path, prefix=prefix))
    all_pkgs = filter(lambda x: x.ispkg, all_module_infos)
    all_modules = itertools.filterfalse(lambda x: x.ispkg, all_module_infos)

    #- packages are already imported by walk_packages() code
    successful_imports = list(all_pkgs)

    for modinfo in all_modules:
        try:
            new_mod = importlib.import_module(modinfo.name)
            successful_imports.append(new_mod)
        except ImportError as err:
            log.warning("Failed to import implementor module: {}: {}".format(\
                modinfo.name, err))

    return successful_imports


def get_implementor_app_name(module):
    """
    Description:
        get the name of the CushApplication object that this implementor is assigned to by
        default.

    Input:
        module: a module name or a module object

    Output:
        Expected name of the cush application to use for this implementor module

    """
    log = LoggerAdapter(logger, {'name_ext':'get_implementor_app_name'})
    top_module_name = 'cush.implementor'
    top_implementor_name_index = len(top_module_name.split('.'))

    if isinstance(module, str):
        module_name = module

    else:
        try:
            module_name = module.__name__
        except AttributeError:
            log.error("Can't get module name from object: {}".format(module))
            return None
            
    try:
        app_name = module_name.split('.')[top_implementor_name_index]
    except TypeError:
        log.warning("Malformed module name; can't get app name from: {}".format(\
                module))
            
    return app_name
