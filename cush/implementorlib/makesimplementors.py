from logging import getLogger, LoggerAdapter

logger = getLogger(__name__)

import abc
import collections
import importlib
import operator
import math
import re
import inspect

from cush import get_cush
from .load import get_implementor_app_name

def make_nsid(_in):
    #- TODO: Any valid Python Identifier should work
    #-     see: https://docs.python.org/3/reference/lexical_analysis.html#identifiers
    """
    Description:
        replace all non alphanumerics with an underscore
    Input:
        what we got that we are trying to make into an NSID
    Output:
        transformed NSID string
    """
    string = str(_in)
    nsid = re.sub('[^a-zA-Z0-9]', '_', _in)
    return nsid

    
def output_nsid(func):
    """
    Description:
        Decorater that takes a function and transforms its output to make it a valid NSID
    """

    def _closure(*args, **kwargs):
        orig_output = func(*args, **kwargs)
        nsid_output = make_nsid(orig_output)
        return nsid_output

    return _closure

class makes_implementors(object):
    """
    Description:
        Decorator class for decorating methods that are used to create implmentor objects.
        Implementors are all hooked up to the runtime namespace to be able to flipped off
        and on at will of the Operator. Implementors create and return objects that are
        thus then controlled by the state of the implementors flipswitch ("on" or "off").
    
        As Implementors create objects, we need a way to keep track of the objects that
        are created by the implmentors so that when an implementors flipswitch state is
        changed, all of the states of the objects associated with that particular
        implementor are also updated in real time.

        In a similar way, the inputs that are used to create implementors can also be
        flipswitched at will and doing so should in turn flip the state of all the
        implementor objects which were created from these inputs.

        This class decorates the 2nd type of method described above.
    """
    #- [pkg_name] -> list of methods decorated with this class
    per_pkg_list = collections.defaultdict(list)

    def __init__(self, nsid, priority=math.inf, key=None,\
        app_name_call=get_implementor_app_name):
        """
        Input:
            nsid: what namespace id to assign to the returned implementor
                objects in the implementor namespace

            priority: numerical specification of what order in which to run this
                implementor provisioner, relative to the other implementor provisioners in
                a given package

            key: a string or a callable object that is called on each output object to
                give us the key to use for this object in the implementor namespace
                If its a string, it is by default converted to a callable via
                operator.attrgetter(key)

            app_name: callable returning name of the top-level application object
        """
        log = LoggerAdapter(logger, {'name_ext': 'makes_implementors.__init__'})
        log.debug("Initializing decorator class with nsid: {} | priority: {}".format(\
            nsid, priority))

        self._nsid = nsid
        self._priority = priority

        #- tag this object so it can be checked by other wrappers like @takes_nsids
        self._makes_implementors = True
        self.app_name_getter = app_name_call

        if callable(key) or key is None:
            self._key = output_nsid(key)
        elif isinstance(key, str):
            self._key = output_nsid(operator.attrgetter(key))
        else:
            raise ValueError("{} key parameter needs to be one of {}".format(\
                self.__class__.__name__, ['callable', 'string', 'None']))
            
        log.debug("Exiting __init__")



    @staticmethod
    def get_root_implementor_pkg_name(module):
        """
        Description:
            get the root implementor package name.
        Input:
            module object
        Output:
            name of the root implementor package. (name below the cush application name)
        """
        top_level_package = 'cush.implementor'
        root_implementor_index = len(top_level_package.split('.')) + 1 #- +1 for app name
        return module.__name__.split('.')[root_implementor_index]




    def __call__(self, func):
        """
        Description:
            we keep track of the input arguments that are used to create this implementor
            object and link the implementor to these inputs

        Input:
            func: the function object being decorated

        Output:
            the closure function object defined below
        """
        log = LoggerAdapter(logger, {'name_ext' : 'makes_implementors.__call__'})
        log.debug("entering __call__")

        self.func = func
        #- decorating replaces the name in the module where the decoration takes place
        #- keep the module object so we can call what we just wrapped from it
        #- this is used in make_implementors() because we need to call the function name
        #- in the module where it was decorated

        self.func_module = inspect.getmodule(func)
        #- get the containing package name of the function object
        log.debug("module package: {}".format(self.func_module.__package__))
        self.app_name = self.app_name_getter(self.func_module)
        log.debug("Using Application name: {}".format(self.app_name))
        self.nsroot = get_cush(self.app_name).nsroot
        self.modify_implementor_key_ns()

        root_implementor_pkg = self.get_root_implementor_pkg_name(self.func_module)

        log.debug("root implementor module package: {}".format(root_implementor_pkg))
        self.per_pkg_list[root_implementor_pkg].append(self)



        def _closure(*args, **kwargs):
            """
            Description:
                this the actual callable that will be returned and then called every time
                the decorated function is called. For all the inputs that are subclasses
                of ImplementorInput, or support the methods "add_child()" and
                "add_children()", We keep track of the inputs that are passed as
                parameters to the original method and the outputs resulting from the call
                of the original method with those inputs by adding the outputs to the list
                of children for each input.

            Input:
                *args: the runtime list of parameters passed to the original function call
            """
                
            log = LoggerAdapter(logger, {'name_ext' :\
                'makes_implementors.___call__._closure'})
            log.debug("closure (and original function) params: [{}]".format(args))

            func_input = dict(args=args, kwargs=kwargs)
            log.debug("Adding inputs to implmentor input namespace")
            inputs_with_nsids = self.modify_implementor_input_ns(func_input)

            func_output = func(*args, **kwargs)

            log.debug("original function output: {}".format(func_output))
            log.debug("adding output to implementor namespace at :{}".format(self._nsid))
            if func_output is None:
                msg1 = "Implementor Provisioner {} returned None".format(self.func.__name__)
                msg2 = "implementors.{} as None probably isn't what you want..".format(\
                    self._nsid)
                log.warning(msg1)
                log.warning(msg2)
                    

            implementors = func_output
            self.modify_implementor_ns(implementors)

            log.debug("Returning from internal closure")
            return func_output
            #- end _closure function definition


        log.debug("Returning closure object to be called")
        self.modify_implementor_provisioner_ns(_closure)
        #- let @takes_nsids know this closure should be overwritten
        #- if it is also wrapped in @takes_nsids
        _closure._makes_implementors = True
        _closure._nsid = self._nsid
        return _closure



    def modify_implementor_provisioner_ns(self, provisioner):
        """
        Description:
            add the function object used to provision the implementors into the
            implementor provisioner namespace
        Input:
            provisioner: the function object wrapped by this call
        Output:
            None; modifies implementor_provisioner_namespace directly

        """
        log = LoggerAdapter(logger, {'name_ext' :\
            'makes_implementors.modify_implementor_provisioner_ns'})
        log.debug("Adding function to implementor provisioners: {}".format(\
            provisioner))
        self.nsroot.implementor_provisioner.add_item(self._nsid, provisioner)
        return


    def modify_implementor_input_ns(self, inputs):
        """
        Description:
            add the input objects to the implementor provisioning function as raw objects
            in the implmementor input namespace
        Input:
            inputs: dictionary that describes what will be added to the implementor input
            namespace. Every item to be added will be added underneath the node rooted at
            self._nsid with a sub-key defined in the dictionary key. As used here, this is
            the dictionary of keyword arguments.

        Output:
            a list of tuples of (nsid, implmentor_input) that was added to the
            implementor_input namespace

        Notes:
            directly modifies implementor_input namespace
        """
        log = LoggerAdapter(logger, {'name_ext' :\
            'makes_implementors.modify_implementor_ns'})
        log.debug("Inputs to be added to Implementor Input Namespace: {}".format(inputs))
        f_args, f_kwargs = inputs['args'], inputs['kwargs']

        #- expect that the first arg is for the original args to be passed back
        #- if they are using @takes_nsids to overwrite the args with NSID lookups
        #- thus, the positional args can have an expected length of one
        if len(f_args) > 1:
            msg = "Can only add implementor inputs to namespace if they are keyword-only"
            msg += ". Skipping positional arguments"
            log.warning(msg)

        inputs_with_nsids = list()
        for k,v in f_kwargs.items():
            subkey = k
            nsid = '.'.join([self._nsid, subkey])
            self.nsroot.implementor_input.add_item(nsid, v)
            inputs_with_nsids.append( (nsid, v) )

        return inputs_with_nsids




    def modify_implementor_ns(self, implementor_objs):
        """
        Description:
            get an NSID for each implementor object and add it to the implementor
            namespace under this new id
        """
        log = LoggerAdapter(logger, {'name_ext':\
            'makes_implementors.modify_implementors_ns'})
        log.debug("Modifying implementor namespace with: implementors: {}".format(\
            implementor_objs))

        if self._key is None:
            #- add them all raw
            self.nsroot.implementor.add_item(self._nsid, implementor_objs)

        else:
            for implementor in implementor_objs:
                sub_nsid = self._key(implementor)
                nsid = '.'.join([self._nsid, sub_nsid])
                self.nsroot.implementor.add_item(nsid, implementor)
                    

    def modify_implementor_key_ns(self):
        """
        Description:
            add the method used for the key to the implementor key namespace
        """
        self.nsroot.implementor_key.add_item(self._nsid, self._key)


    @classmethod
    def make_implementors(cls, pkgs=None):
        """
        Description:
            order the implementor provisioners by user set priority and call them in order

        Input:
            pkgs: optional list of packages to make the implementors for. Defaults to all.
        """
            
        log = LoggerAdapter(logger, {'name_ext': 'makes_implementors.make_implementors'})
        if pkgs is None:
            pkgs = cls.per_pkg_list.keys()

        for pkg in pkgs:
            cls.per_pkg_list[pkg].sort(key=operator.attrgetter('_priority'))

            log.debug("per_pkg_list[{}]: {}".format(pkg, cls.per_pkg_list[pkg]))
            for provisioner in cls.per_pkg_list[pkg]:
                log.debug("provisioner: {}".format(provisioner))
                try:
                    #- call it from the module where it was originally defined
                    provisioner.func_module.provision_implementors()

                except (AttributeError, TypeError) as err:
                    log.error("Failed to provision implementors for module: {}".format(\
                        pkg))
                    log.exception(err)

            
    def __repr__(self):
        repr = "makes_implementors(nsid={}, priority={})".format(self._nsid, self._priority)
        return repr
