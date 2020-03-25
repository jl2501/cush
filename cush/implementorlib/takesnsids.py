import abc
import collections
import inspect

import logging
from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

from cush import get_cush


class takes_nsids(object):
    """
    Description:
        Decorator class for decorating methods that need inputs from the implmentor
        namespace. As the implmentation is arbitrary and out of our control, but we have a
        specific way to load implmentor packages, we use this decorator to write methods
        that may need some implmentation objects in place before they can work, but we
        don't want the user to have to create these implmentation object mulitple times
        just to plug in to the framework. This decorator allows users to write methods
        that will need access to implmentational objects when they run and take those
        objects as an ordered sequence of parameters that will be bound to the objects
        that occupy the given namespace ids at runtime
    """
    def __init__(self, func, app_name='default'):
        """
        Input:
            *args: variable list of implementor namespace ids that will be bound to the
                parameters of the decorated function.
        """
        log = LoggerAdapter(logger, {'name_ext': 'takes_nsids.__init__'})
        log.debug("Decorating {}".format(func))
        self._func = func
        self.nsroot = get_cush(app_name).nsroot

        try:
            nsid = self._func._nsid
            #- overwrite makes_implementors closure in implementor provisioners namespace
            if self._func._makes_implementors:
                log.debug("(Over)writing function in implementor provisioners")
                self.nsroot.implementor_provisioner.add_item(namespace_id=nsid,\
                    value=self.__call__, overwrite=True)

        except AttributeError:
            #- this is not an implementor provisioner
            #- so, don't add this to implementor provisioners ns
            log.debug("Function has no NSID set")
            pass

        log.debug("Exiting __init__")

    def __call__(self, *args, **kwargs):
        """
        Description:
            this the actual callable that will be returned and then called every time
            the decorated function is called. For all the inputs that are subclasses
            of Flipswitch, or support the methods "add_child()" and
            "add_children()", We keep track of the inputs that are passed as
            parameters to the original method and the outputs resulting from the call
            of the original method with those inputs by adding the outputs to the list
            of children for each input.

            TODO: We then create new flipswitches in the runtime namespace for all the
            inputs and outputs.

        Input:
            *args: the runtime list of parameters passed to the original function call
        """
            
        log = LoggerAdapter(logger, {'name_ext' : 'takes_nsids.___call__._closure'})
        log.debug("closure (and original function) params: [{}]".format(args))

        f = self.get_original_function(self._func)
        arg_spec = inspect.getfullargspec(f)
        nsid_args = arg_spec.kwonlydefaults

        kwarg_names = nsid_args.keys()
        final_kwargs = dict()
        #- put the original args in here
        final_args = dict()
        for kwarg_name in kwarg_names:
            nsid = nsid_args[kwarg_name]
            final_args[kwarg_name] = nsid
            final_kwargs[kwarg_name] = self.nsroot._lookup(nsid)

        final_args['nsid'] = self.get_implementors_nsid(self._func)
        log.debug("Calling method with args: |{}|".format(final_args))
        log.debug("Calling method with kwargs: |{}|".format(final_kwargs))
        func_output = self._func(final_args, **final_kwargs)
        log.debug("Function output: {}".format(func_output))
        return func_output

    @staticmethod
    def is_makes_implementors(f):
        """
        Description:
            True if the function we are wrapping was wrapped by @makes_implementors first
            False otherwise

        Notes:
            will return True for any class that has the attribute "_makes_implementors"
            set to a non-False value
        """
        log = LoggerAdapter(logger, {'name_ext' : 'takes_nsids.is_makes_implementors'})
        try:
            #- deal with case where func is wrapped inside of @makes_implementors
            #- XXX assumes that this is wrapped by @makes_implementors
            #-    or, equivalently, a class-based closure that has the
            #-    wrapped function stored as "self.func"
            #-
            #-    inspect.unwrap() doesn't seem to work for this closure
            #-    as the closure is in __closure__[0].cell_contents, not in
            #-    __wrapped__. Not sure if that's a bug?
            tag = inspect.getclosurevars(f).nonlocals['self']._makes_implementors
            return bool(tag)
        except AttributeError as err:
            log.debug("doesn't look like this was wrapped with @makes_implementors")
            return False


    def get_original_function(self, f):
        """
        Description:
            Deals with getting the original function object in the case that it is wrapped
            inside a closure from @makes_implementors

        Input:
            f: function or a closure generated by @makes_implementors

        Notes:
            will work for any class-based decorator that stores the function as
            "self.func"
        """
        if self.is_makes_implementors(f):
            return inspect.getclosurevars(f).nonlocals['self'].func
        else:
            return f

    
    def get_implementors_nsid(self, f):
        """
        Description:
            gets the 'nsid' attribute from the underlying closure class, if
            possible
        """
        if self.is_makes_implementors(f):
            return inspect.getclosurevars(f).nonlocals['self']._nsid
        else:
            return None
