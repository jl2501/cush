import cush.defaults as defaults
import os
import collections
from thewired import get_provider_classes
import ruamel.yaml


from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)


def filename_to_fullpath(directory=None, filename=None):
    """simple utility to translate an unexpanded path and filename into
    something we can pass directly to open"""

    if directory is None or filename is None:
        err_msg = "filename_to_filepath: can't create path from null directory nor null filename: {}, {}".format(
                str(directory), str(filename))
        raise ValueError(err_msg)

    #- create pathname from dir, filename
    path = os.path.join(directory, filename)
    path = os.path.expandvars(path)
    path = os.path.expanduser(path)
    path = os.path.realpath(path)

    return path



def load_yaml_file(filename=None, dir=defaults.config_dir):
    """
    load and parse YAML into a dict
    """

    log = LoggerAdapter(logger, {'name_ext' : 'load_yaml_file'})
    if filename is None:
        raise ValueError("load_yaml_file: need a filename to load.")

    config_filepath = filename_to_fullpath(dir, filename)

    yaml_dict = dict()
    with open(config_filepath, 'rt') as fp:
        try:
            yaml_dict = ruamel.yaml.load(fp, ruamel.yaml.RoundTripLoader)
        except ruamel.yaml.YAMLError as err:
            log.error('load_yaml_file: Error loading {}: {}'.format(config_filepath, str(err)))
    return yaml_dict



class ClassTable(collections.UserDict):
    def __init__(self, cls_list):
        '''
        Description:
            build a mapping of class.__name__s --> class objects

        Input:
            initial_list: list of class instances

        Output:
            a dict mapping of [class name] -> class object

        '''
        super().__init__()

        for cls in cls_list:
            #- strip the import namespacing, just leave the class name
            class_lookup_name = cls.__name__.split('.')[-1]
            self.data[class_lookup_name] = cls


class ProviderClassTable(object):
    """
    Description:
        Singleton ClassTable of all the available provider classes.
        Updates every time it is instantiated.

        This is basically a simple way to wrap away the get_provider_classes() method and
        provide some kind of way to iterate and inspect the available providers.

    Notes:
        Initially this was going to be a ProviderNamespace, but there really doesn't seem
        to be a need for a namespace for these as they are already organized in the class
        hierarchy and namespaced according to the package-level / import namespace.

    """
    def __new__(cls):
        #- always update and have only one
        return ClassTable(get_provider_classes())



