__version__ = 0.0.1

import logging
import logging.config
from .app import CushApplication, get_cush


step_initialize=True
init_namespaces = ['user', 'implementor', 'default', 'param', 'provider', 'sdk']

def init_cush(application_name='default', step=step_initialize,
        namespaces=init_namespaces, overwrite=True):
    """
    call this after importing to initialize the cush namespaces

    application_name: name of the cush application to initialize
    step: prompt before initializing each section of the application
    namespaces: list of which namespaces to initialize
    overwrite: whether or not to overwrite existing nodes
    """
    from cush.util import load_yaml_file
    logging.config.dictConfig(load_yaml_file(filename=defaults.logging_config_file))
    if step:
        x = input("Initializing Bare Application Object: [Enter to continue]")


    from cush.app import CushApplication
    _cushapp = CushApplication(name='default')

    #- mapping of names to init methods
    name_to_init_method = {
        'user' : _cushapp.init_user_namespace,
        'implementor' : _cushapp.init_implementor_namespace,
        'default' : _cushapp.init_default_namespace,
        'param' : _cushapp.init_param_namespace,
        'provider' : _cushapp.init_provider_namespace,
        'sdk' : _cushapp.init_sdk_namespace
    }

    for ns_name in namespaces:
        if step:
            ans = input('Initialize {} Namespace? (y/n) [Y]: '.format(ns_name))
            if ans.lower() in ['y', 'yes', 'ye', '']:
                name_to_init_method[ns_name]()
        else:
            name_to_init_method[ns_name]()


#- setup module-level namespace
applications = CushApplication.nsroot.applications
