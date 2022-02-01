from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

import math
import operator
import collections
import inspect
import itertools
import re
from abc import abstractmethod
from collections.abc import Iterable
from .load import get_implementor_app_name
from functools import partial

from thewired import DelegateNode
from thewired.exceptions import NamespaceLookupError
from thewired.namespace.nsid import make_child_nsid, sanitize_nsid

from cush import get_cush
from cush.user import CushUser
from .flipswitch import Flipswitch


class SimpleWrap(object):
    """
    Serves no point other than to allow keys to be looked up using the implementor
    object as the lookup key when we have no control over implementor objects
    types and thus can not assume they are hashable / able to be used directly as
    dictionary keys

    Only used when figuring out NSIDs of implementors before adding related objects to
    their respective implementor-related namespaces.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.nsid_key = ''
        self.postfix_key = ''


class ImplementorProvisioner(object):
    """
    Description:
        Container object for streamlining process of writing methods that create implementors. 
        Expected workflow is that a user should simply subclass this class and write a single method
        named "make_implementors" (and some boilerplate __init__ to call super().__init__())

        Contains methods and links to the namespaces to take care of:
            * putting the implementors created into the implementor namespace
            * put this ImplementorProvisioner object into the implementor_provisioner
              namespace
            * take care of making the flipswitches that are specified by the user in their
              implementor provisioning method
            * gives access to the implementors namespace so that users can refer to
              existing implementors
            * sorts the provisioner subclasses by priority and creates the implementors in
              the user-specified priority. This makes sure that provisioner methods that
              require access to other implementors have the implementors they need already
              created before they run.
    """

    #- Class Level list keeps track of all subclasses' make_implementors methods
    #- every time an instance of this class is created, the __init__ method keeps track of
    #- the instance in this dict
    #- [pkg_name] -> list of instances of this class or subclasses
    all_provisioners = collections.defaultdict(list)

    @abstractmethod
    def make_implementors(self, *args, **kwargs):
        """
        Description:
            Required user-supplied method that outputs a set of objects to be added to the
            implementor namespace
        """
        log = LoggerAdapter(logger, {'name_ext' :\
            'ImplementorProvisioner.make_implementors'})

        log.debug("Entering")
        log.debug("Input args: {}".format(args))
        log.debug("Input kwargs: {}".format(kwargs))

        log.debug("Exiting")
        return


    @abstractmethod
    def get_nsid_addendum(self, *args, **kwargs):
        """
        Description:
            Optional user-defined method to define the nsid addendum used to namespace out
            different implementors of the same type and root nsid

        Input:
            user-defined

        Output:
            an nsid string that will be appended to the root_nsid
        """
        pass


    @classmethod
    def make_all_implementors(cls, pkgs=None, overwrite=False):
        """
        Description:
            Instantiates the implementor objects. As all Implementors are provisioned /
            instantiated by ImplementorProvisioner subclasses and Python allows us to
            dynamically find all subclasses, to create them, we simply get all the
            subclasses of this class and then call the 'call_make_implementors()' method
            which wraps the 'make_implementors()' method which must be defined by all
            subclasses.

            As some implementors depend on others existing before they are created, this
            will order the implementor provisioners by user set priority and call them in
            order

        Input:
            pkgs: optional list of packages to make the implementors for. Defaults to all.

        Output:
            None directly; adds implementors to the implementor Namespace
        """

        log = LoggerAdapter(logger, {'name_ext': 'ImplementorProvisioner.make_implementors'})
        log.debug("Entering")
        subclasses = cls.__subclasses__()
        log.debug("Found subclasses: {}".format(subclasses))
        instances = list()

        #- instantiate all the implementors
        #- as each implementor is a different subclass, this works
        for subclass in subclasses:
            instances.append(subclass())
        log.debug("Instantiated: {}".format(instances))

        if pkgs is None:
            pkgs = cls.all_provisioners.keys()
            log.debug("pkgs: {}".format(pkgs))

        #- make a single iterable, sorted by priority
        all_pkg_provisioners = cls.all_provisioners.values()
        provisioners_iter = itertools.chain.from_iterable(all_pkg_provisioners)
        provisioners = sorted(provisioners_iter, key=operator.attrgetter('priority'))
        log.debug("sorted provisioners: {}".format(provisioners))

        for provisioner in provisioners:
            log.debug("provisioner: {}".format(provisioner))
            try:
                #- call it from the module where it was originally defined
                #- this call modifies the implementor namespaces
                provisioner.call_make_implementors(overwrite=overwrite)

            except (AttributeError, TypeError) as err:
                log.error("Failed to provision implementors: {}".format(\
                    provisioner))
                log.exception(err)
        log.debug("Exiting")



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
        #- +1 for CushApplication name ("default" by default)
        root_implementor_index = len(top_level_package.split('.')) + 1
        return module.__name__.split('.')[root_implementor_index]





    def __init__(self, root_nsid, priority=math.inf, nsid_exts=None, **kwargs):
        """
        Users of this class must call super().__init__(priority) to correctly set the
        priority of their make_implementors method
        """
        log = LoggerAdapter(logger, {'name_ext' : 'ImplementorProvisoner.__init__'})
        msgs = list()
        msgs.append("Entering __init__: root_nsid: {}".format(root_nsid))
        #msgs.append("priority: {}  |  key: {}  |  postfix_key:  {}".format(\
        #        priority, key, postfix_key))
        msgs.append("priority: {} nsid_exts: {}".format(priority, nsid_exts))
        log.debug('::'.join(msgs))


        self.root_nsid = root_nsid
        self.priority = priority

        module = inspect.getmodule(self)
        module_pkg = self.get_root_implementor_pkg_name(module)
        log.debug("module package: {}".format(module.__package__))

        self.app_name = get_implementor_app_name(module)
        log.debug("Using Application name: {}".format(self.app_name))

        self.cush = get_cush(self.app_name)
        self.nsroots = dict(
                root=self.cush._ns.root,

                implementor=self.cush._ns.get_handle('.implementor'),
                implementor_input=self.cush._ns.get_handle('.implementor_input'),
                implementor_provisioner=self.cush._ns.get_handle('.implementor_provisioner'),

                flipswitch=self.cush._ns.get_handle('.flipswitch'))

        root_implementor_pkg = self.get_root_implementor_pkg_name(module)
        log.debug("root implementor module package: {}".format(root_implementor_pkg))


        self.nsid_exts = list() if nsid_exts is None else nsid_exts
        if 'key' in kwargs.keys():
            self.nsid_exts.append(self.wrap_nsid_ext(kwargs['key']))

        if 'postfix_key' in kwargs.keys():
            self.nsid_exts.append(self.wrap_nsid_ext(kwargs['postfix_key']))


        self.all_provisioners[root_implementor_pkg].append(self)
        log.debug("Exiting")


    def wrap_nsid_ext(self, nsid_ext):
        if callable(nsid_ext):
            nsid_extfunc = self.output_nsid(nsid_ext)
        elif isinstance(nsid_ext, str):
            nsid_extfunc = self.output_nsid(operator.attrgetter(nsid_ext))
        else:
            raise ValueError("{} nsid_ext parameter needs to be one of {}".format(\
                self.__class__.__name__, ['callable', 'string', 'None']))
        return nsid_extfunc



    def add_nsid_ext(self, nsid_ext):
        """
        Description:
            Adds an NSID extension to the list of them
            Takes care of all the NSID-specifics such as char substitution.
        Input:
            nsid_ext: nsid extender; callable or a string. If it's a callable, will be
            called with an implementor as an argument. If a string, the string will be
            unconditionally appended.
        Output:
            None; modifies and stores nsid_ext as an NSID extender.
        """
        name_ext = {'name_ext' : '{}.add_nsid_ext'.format(self.__class__.__name__)}
        log = LoggerAdapter(logger, name_ext)
        log.debug("Entering")

        wrapped_func = self.wrap_nsid_ext(nsid_ext)
        log.debug("Generated wrapped function: {}".format(wrapped_func))

        self.nsid_exts.append(wrapped_func)
        log.debug("Exiting")

    def get_nsid_ext(self, imp):
        """
        Description:
            get the NSID extension for the implementor imp
        Input:
            imp: implementor object to compute NSID of
        Output:
            NSID extension of implementor object imp

        Notes:
            this method will replace the old key and postfix_key methods for computing
            extra NSID components of an implementor
        """
        log_name_ext = f"{self.__class__.__name__}.get_nsid_ext"
        log = LoggerAdapter(logger, dict(name_ext= log_name_ext))
        log.debug("Enter")
        log.debug("self.nsid_exts: {}".format(self.nsid_exts))

        nsid_exts = list()
        for nsid_extender in self.nsid_exts:
            if callable(nsid_extender):
                log.debug("generating nsid_ext from callable")
                nsid_ext = nsid_extender(imp)
                log.debug(f"callable generated nsid_ext: {nsid_ext}")
                nsid_exts.append(nsid_ext)
            elif isinstance(nsid_extender, str):
                log.debug(f"adding nsid_ext string: {nsid_extender}")
                nsid_exts.append(nsid_extender)

        log.debug('pre-filter nsid_exts: {}'.format(nsid_exts))
        final_nsid_extension = sanitize_nsid('.'.join(filter(lambda x: x and isinstance(x, str), nsid_exts)))
        log.debug("final_nsid_extension: {}".format(final_nsid_extension))
        return final_nsid_extension




    def get_nsid_addendum(self, implementor):
        """
        Description:
            create the full, unique NSID for this implementor object using the key and
            postfix_key

        Input:
            implementor: the implementor object to generate NSID for

        Output:
            the full NSID, with all addendums based on key and postfix functions
        """
        name_ext = {'name_ext' : 'ImplementorProvisioner.get_nsid_addendum'}
        log = LoggerAdapter(logger, name_ext)
        log.debug("making nsid addendum for: {} | root_nsid: {}".format(implementor,\
                self.root_nsid))

        if self.key:
            key_addendum = self.key(implementor)
            log.debug("key addendum: {}".format(key_addendum))
        else:
            key_addendum = ''
            log.debug("no key function found")
        if self.postfix_key:
            postfix_key_addendum = self.postfix_key(implementor)
            log.debug("postfix_key addendum: {}".format(postfix_key_addendum))
        else:
            postfix_key_addendum = ''
            log.debug("no postfix_key function found")

        addendum = '.'.join(filter(None, [key_addendum, postfix_key_addendum]))
        log.debug("returning final addendum: {}".format(addendum))
        return addendum



    def get_full_nsid(self, imp):
        """
        Description:
            get the full nsid (root + all addendums) for an implementor

        Input:
            imp: implementor  object

        Output:
            full nsid
        """
        return '.'.join([self.root_nsid, self.get_nsid_ext(imp)])



    def call_make_implementors(self, overwrite=False):
        """
        Description:
            Wrapper around the user/subclass defined make_implementors method to perform
            the namespace modifications needed after the implementors are created.

        Input:
            None; uses self to call user-defined make_implementors() on the user-defined 
            ImplementorProvisioner subclass

        Output:
            None; the following cush namespaces are directly modified:
                * implementor_input
                * implementor
                * implementor_provisioner
        """
        log = LoggerAdapter(logger, {'name_ext' :\
            'ImplementorProvisioner.call_make_implementors'})
        log.debug("Entering")

        log.debug("Calling user-defined make_implementors() method")
        fresh_implementors = self.make_implementors()

        log.debug("user-defined make_implementors() output: {}".format(fresh_implementors))
        log.debug("instance root_nsid: {}".format(self.root_nsid))

        if fresh_implementors is None:
            msg1 = "Implementor Provisioner {} returned None".format(self.func.__name__)
            msg2 = "implementors.{} as None probably isn't what you want..".format(\
                self.root_nsid)
            log.warning(msg1)
            log.warning(msg2)


        log.debug("Modifying implementor_input namespace")
        #- we get the inputs from the method signature of the user-defined method
        argspec = inspect.getfullargspec(self.make_implementors)
        inputs_with_nsids = self.modify_implementor_input_ns(argspec, overwrite=overwrite)


        log.debug("Modifying implementor namespace")
        self.modify_implementor_ns(fresh_implementors, overwrite=overwrite)

        log.debug("Modifying implementor_provisioner namespace")
        self.modify_implementor_provisioner_ns(overwrite=overwrite)
        log.debug("Exiting")
        return


    def modify_implementor_provisioner_ns(self, overwrite=False):
        """
        Description:
            add self into the implementor provisioner namespace
        Input:
            provisioner: the function object wrapped by this call
        Output:
            None; modifies implementor_provisioner_namespace directly
        """
        log = LoggerAdapter(logger, {'name_ext' :\
            'ImplementorProvisioner.modify_implementor_provisioner_ns'})
        log.debug("Entering")
        log.debug("Adding self to implementor provisioner ns: {}".format(\
            self))

        #- TODO: calculate and use NSID postfix
        node_factory = partial(DelegateNode, self)
        self.nsroots['implementor_provisioner'].add(self.root_nsid, node_factory)
        log.debug("Exiting")
        return




    def modify_implementor_input_ns(self, argspec, overwrite=False):
        """
        Description:
            add the input objects to the implementor provisioning function as raw objects
            in the implmementor input namespace
        Input:
            inputs: dictionary that describes what will be added to the implementor input
            namespace. Every item to be added will be added underneath the node rooted at
            self.root_nsid with a sub-key defined in the dictionary key. As used here, this is
            the dictionary of keyword arguments.

        Output:
            a list of tuples of (nsid, implmentor_input) that was added to the
            implementor_input namespace

        Notes:
            directly modifies implementor_input namespace
        """
        log = LoggerAdapter(logger, {'name_ext' :\
            'ImplementorProvisioner.modify_implementor_input_ns'})
        log.debug("Entering")
        log.debug("Inputs to be added to Implementor Input Namespace: {}".format(argspec))

        inputs_with_nsids = list()
        if len(argspec.args) > 1:
            iter1 = zip(argspec.args[1:], argspec.defaults)
        else:
            iter1 = list()

        if argspec.kwonlydefaults:
            iter2 = argspec.kwonlydefaults.items()
        else:
            iter2 = list()
        arg_and_kwarg_specs = itertools.chain(iter1, iter2)

        #- TODO: calculate and use NSID postfix
        for k,v in arg_and_kwarg_specs:
            subkey = k
            nsid = '.'.join([self.root_nsid, subkey])
            log.debug(f"adding implementor_input node: {nsid=}")
            self.nsroots['implementor_input'].add(nsid, DelegateNode, v)
            inputs_with_nsids.append((nsid, v))
        log.debug("Exiting")
        return inputs_with_nsids



    def modify_implementor_ns(self, implementor_objs, overwrite=False):
        """
        Description:
            get an NSID for each implementor object and add it to the implementor
            namespace under this new id
        """
        log = LoggerAdapter(logger, {'name_ext':\
            'ImplementorProvisioner.modify_implementor_ns'})
        log.debug("Entering")
        log.debug("Modifying implementor namespace with: implementors: {}".format(\
            implementor_objs))

        for imp in implementor_objs:
            full_nsid = f".{self.get_full_nsid(imp)}"
            log.debug(f"adding item to implementor ns:  {full_nsid}--->{imp}")

            node_factory = partial(DelegateNode, imp)
            self.nsroots['implementor'].add(full_nsid, node_factory)

        log.debug("Exiting")


    def lookup_implementor(self, implementor_nsid):
        """
        Description:
            Method for users to be able to lookup existing implementors by nsid
        """
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.lookup_implementor"))
        log.debug(f"called with: {implementor_nsid=}")
        #subnodes = self.implementor_ns_root.get_subnodes(f".{implementor_nsid}")
        subnodes = self.cush._ns.get_subnodes(f".implementor.{implementor_nsid}")
        return filter(lambda x: isinstance(x, DelegateNode), subnodes)


    def lookup_user(self, user_nsid):
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.lookup_user"))
        log.debug(f"called with: {user_nsid=}")
        subnodes = self.cush._ns.get_subnodes(f'.user.{user_nsid}')
        return filter(lambda x: isinstance(x, CushUser), subnodes)


    def make_flipswitch(self, implementor, app_name='default', prefix=None):
        """
        Description:
            Module-level utility method to be used by client code that wishes to create a
            flipswitch from an object.

        Input:
            obj: the object to make into a flipswitch

        Output:
            a Flipswitch for object
        """
        log = LoggerAdapter(logger, {'name_ext' :\
            'ImplementorProvisioner.make_flipswitch'})
        log.debug("Entering")

        imp = implementor
        #- make nsid
        full_nsid = self.get_full_nsid(imp)
        log.debug("flipswitch starting full_nsid: {}".format(full_nsid))

        #full_nsid = self.cush._ns.root.nsid + '.implementor.' + full_nsid
        full_nsid = make_child_nsid(str(self.implementor_ns_root.nsid), full_nsid)
        log.debug("final flipswitch full_nsid: {}".format(full_nsid))

        ###fs = Flipswitch(full_nsid, self.nsroot)

        fs = self.cush._ns.add('.flipswitch' + full_nsid, node_factory=Flipswitch)
        log.debug("Exiting")
        return fs


    def link_flipswitches(self, parent, children, app_name='default'):
        """
        Description:
            Link the parent to control the flipswitch of the child flipswitch

        Input:
            parent: a Flipswtich-like object or an NSID of a parent
            child: a Flipswitch-like object or an Iterable of Flipswitch-like objects

        Output:
            None; adds the children to the parent
        """
        log = LoggerAdapter(logger, {'name_ext': 'link_flipswitches'})
        log.debug("Entering")
        log.debug("Linking flipswitches: {} ---> {}".format(parent, children))

        if not parent:
            log.warning("Can't link parent: {}".format(parent))
            log.debug("Exiting")
            return

        if isinstance(children, str) or\
            not isinstance(children, Iterable):
            children = [children]

        if isinstance(parent, str):
            #- treat as an existing NSID
            parent = self.cush._ns.root.flipswitch.get(parent)

        if not isinstance(parent, Iterable):
            parents = [parent]
        else:
            parents = parent

        for _parent in parents:
            _parent.add_children(children)
        log.debug("Exiting")
        return


    @staticmethod
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
        _string = str(_in)
        nsid = re.sub('[^a-zA-Z0-9.]', '_', _string)
        return nsid


    @staticmethod
    def output_nsid(func):
        """
        Description:
            Decorater that takes a function and transforms its output to make it a valid NSID
        """
        def _closure(*args, **kwargs):
            log = LoggerAdapter(logger, dict(name_ext=f"output_nsid-CLOSURE: {func=}"))

            orig_output = func(*args, **kwargs)
            log.debug(f"{orig_output=}")

            nsid_output = ImplementorProvisioner.make_nsid(orig_output)
            log.debug(f"{nsid_output}")

            return nsid_output

        return _closure



    def get_flipswitch_from_implementor(self, base_nsid, implementor):
        """
        Description:
            lookup an implementors flipswitch, if it exists
        """

        log = LoggerAdapter(logger, {'name_ext' :\
            'ImplementorProvisioner.get_flipswitch_from_implementor'})
        log.debug("Entering: base_nsid: {}".format(base_nsid))

        Provisioner = self.cush._ns.get(f".implementor_provisioner.{base_nsid}")
        implementor_nsid = Provisioner.get_full_nsid(implementor)

        log.debug("Searching for implementor fs nsid: {}".format(implementor_nsid))
        try:
            full_implementor_nsid = make_child_nsid(str(self.nsroots['implementor'].nsid), implementor_nsid)
            implementor_fs = self.nsroots['flipswitch'].get(f'{full_implementor_nsid}')

            log.debug("Exiting")
            return implementor_fs

        except NamespaceLookupError as err:
            log.warning("Failed to get flipswitch for implementor: {}".format(implementor))
            log.debug("Exiting")
            return None


    def get_flipswitch_from_user(self, user_root_nsid, user):
        """
        Description:
            get the user flipswitch object for a specific user.
        Input:
            user_root_nsid: where the user object is rooted in the users namespace
            user: the specific user
        """
        log = LoggerAdapter(logger, {'name_ext':
                'ImplementorProvisioner.get_flipswitch_from_user'})

        for leaf in self.cush._ns.get_subnodes('.user'):
            if leaf == user:
                user_fs_nsid = leaf.nsid
                log.debug("using flipswitch nsid: {}".format(user_fs_nsid))
                return self.cush._ns.get(f".flipswitch{user_fs_nsid}")



    def __repr__(self):
        repr = "ImplementorProvisioner(nsid={}, priority={})".format(self.root_nsid, self.priority)
        return repr
