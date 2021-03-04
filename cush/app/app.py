import copy
import os

from thewired import NamespaceNode, NamespaceConfigParser, NamespaceLookupError, Namespace, Nsid, NamespaceNodeBase
from thewired import NamespaceConfigParser2
from thewired.namespace.nsid import make_child_nsid

from cush.util import ProviderClassTable
import cush.configuration as configuration
import cush.defaults as defaults
from cush.util import load_yaml_file
from cush.namespace import SdkConfigParser, ProviderConfigParser
from cush.namespace import ParamConfigParser
import cush.implementorlib as implementorlib
from cush.implementorlib.flipswitch import Flipswitch
import cush.implementor


from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)


class CushApplication(NamespaceNodeBase):
    """
    Description:
        Container for the application state
    """
    #- app_name -> application instance mapping
    #- allows us to have multiple CushApplication objects at once
    #- each one will have its own setup if needed
    _applications = dict()

    @classmethod 
    def get_application(cls, name='default'):
        """
        Description:
            get a named application object from the class' list of instances by name
        """
        log = LoggerAdapter(logger, dict(name_prefix='CushApplication.get_application'))
        try:
            app = cls._applications[name]
        except KeyError:
            log.warning("No application object named: {}".format(name))
            log.warning("   available names: {}".format(list(cls._applications.keys())))
            app = None
        return app



    def __new__(cls, name='default', *args, **kwargs):
        log = LoggerAdapter(logger, dict(name_ext='CushApplication.__new__'))
        try:
            app = cls._applications[name]
            log.debug("Found existing application named: {}".format(name))

        except (KeyError, NamespaceLookupError):
            log.debug("Creating new application object named: {}".format(name))
            app = super().__new__(cls)

        return app



    def __init__(self, name='default', namespace=None):
        """
        Input:
            name: application object name
            namespace: the namespace object that contains this cush application
        """
        log = LoggerAdapter(logger, dict(name_ext='CushApplication.__init__'))
        log.debug("Entering")

        #- add self to the class level named list of application object instances
        if name in self._applications.keys():
            #- do not reinitialize existing application object
            log.debug("skipping initialization: CushApplication object already initialized")
            return

        #- else, we are a new CushApplication instance
        #- so go through all the initialization as normal
        self.name = name
        self._ns = namespace

        #- initialize the NamespaceNodeBase stuff
        super().__init__(make_child_nsid('.application', f'{self.name}'), self._ns)


        #- save this instance of CushApplication object to be looked up by name
        CushApplication._applications[self.name] = self

        self._create_cush_namespaces()

        log.debug('****** finished initializing CushApplication')
        log.debug("Exiting")


    def _create_cush_namespaces(self):
        """
        Description:
            cush has a set of expected namespaces that need to all be in place
            for the env to work

            this is where we set all of them up

        Input:
            None
        Output:
            None
        Side-Effects:
            manipulates the containing namespace to add the expected set
        """
        cush_namespaces = [
                "flipswtich",
                "user",
                "implementor",
                "implementor_input",
                "implementor_provisioner",
                "default",
                "param",
                "provider",
                "sdk",
                "ui",
                "formatter" #TODO
        ]
        for nsname in cush_namespaces:
            self._ns.add_exactly_one('.'+nsname)


    def init_user_namespace(self):
        """
        Description:
            Initialize new style user namespace
        """
        log = LoggerAdapter(logger, {'name_ext' : 'CushApplication.init_user_namespace'})
        log.debug("Entering")
        log.info('Initializing user namespace...')

        """
        TODOS
        remove node, sub with _ns
        update userconfigparser to use NamespaceConfigParser2
        """

        user_ns_handle = self._ns.get_handle('.user', create_nodes=True)
        user_ns_parser = NamespaceConfigParser2(namespace=user_ns_handle)
        dictConfig = load_yaml_file(defaults.user_file)
        user_ns_parser.parse(dictConfig)

        #- create empty controlling flipswitches for each user / credential object loaded
        #for nsid, user in root_node._list_leaves(nsids=True):
        #    fs = Flipswitch(nsid=nsid, nsroot=self.app_nsroot)
        #    self.flipswitch._add_item(nsid, fs)
        #log.debug("Exiting")


    def init_implementor_namespace(self, mock=False, overwrite=True):
        """
        Description:
            initialize the implmentor namespace collection
        Load the Implementor objects and place them into a namespace
        """
        
        log = LoggerAdapter(logger, {'name_ext' :\
            'CushApplication.init_implementor_namespace'})

        log.debug("Entering")
        log.info("Initializing implementors namespace...")

        #- return value for debugging. The effect of this is to alter the run-time
        #- namespace by 'import'ing the available modules
        _implementors = implementorlib.load_implementors(app_name=self.name)

        log.debug("Loaded implementors: {}".format(_implementors))
        self._make_implementors(overwrite=overwrite)
        log.debug("Exiting")
        return


    #- Note: this doesn't need to be passed a reference to the CushApplication object
    #-       because it will dynamically get the applicaiton object from the name of
    #-       the ImplementorProvisioner module, which, by default, is taken from the
    #-       name of the module as defined by the filesystem layout
    def _make_implementors(self, overwrite=False):
        """
        Description:
            actually create all the implementor objects

        Input:
            None directly, but calls ImplementorProvisioner.make_all_implementors(),
                which relies on collecting the subclasses of ImplementorProvisioner and
                then instantating them

        Output:
            None. directly modifies the following cush namespaces:
                * implementors
                * implementor_provisioners

        Notes:
           We have to put an import inside this method, rather than at the top of
           this module due to a circular dependecy at import time, but not at run-time.

           implementor_provisioner class uses 'get_cush' method, which is defined in this
           class.

           Thus, we have to instantiate this class before we can import
           makes_implementors, or else we get a circular import problem :-/
        """
        log = LoggerAdapter(logger, {'name_ext' : 'CushApplication._make_implementors'})
        log.debug("Entering")
        #- circular dependency at import time; OK at run-time.
        from cush.implementorlib.implementorprovisioner import\
            ImplementorProvisioner

        ImplementorProvisioner.make_all_implementors(overwrite=overwrite)
        log.debug("Exiting")



    def init_default_namespace(self, node=None):
        """
        Description:
            parse the config for and create the defaults namespace
        Input:
            node: NamespaceNode to use as root. (defaults to self.defaults)
        """
        log = LoggerAdapter(logger, {'name_ext': 'CushApplication.init_default_namespace'})
        log.debug("Entering")
        log.info("Initializing Defaults Namespace...")
        node = self.default if node is None else node
        dictConfig = load_yaml_file(defaults.defaults_ns_file)
        parser = NamespaceConfigParser(prefix='default', nsroot=self.app_nsroot)
        ns_roots = parser.parse(dictConfig)
        for ns_x in ns_roots:
            node._add_ns(ns_x)

        log.debug("Exiting")


    def init_param_namespace(self, node=None):
        """
        Description:
            parse config and create parameters namespace
        Input:
            node: root node of the parameters namespace. (defaults to self.params)
        """
        log = LoggerAdapter(logger, {'name_ext': 'CushApplication.init_parameter_namespace'})
        log.debug("Entering")
        log.info("Initializing Parameters Namespace...")
        node = self.param if node is None else node
        self.param.nsroot = self.app_nsroot
        dictConfig = load_yaml_file(defaults.params_ns_file)

        parser = ParamConfigParser(node, nsroot=self.app_nsroot)

        params_ns_roots = parser.parse(dictConfig)
        for ns_root in params_ns_roots:
            node._add_ns(ns_root)

        log.debug("Exiting")


    def init_provider_namespace(self, node=None):
        log = LoggerAdapter(logger, {'name_ext' :\
            'CushApplication.init_provider_namespace'})

        log.debug("Entering")
        log.info("Initializing provider namespace...")
        if node is None:
            node = self.provider

        dictConfig = load_yaml_file(defaults.providers_ns_file)
        pct = ProviderClassTable()
        parser = ProviderConfigParser(\
            implementor_ns=self.implementor,\
            implementor_state_ns=self.flipswitch,\
            provider_ns=node,\
            nsroot=self.app_nsroot,\
            provider_cls_tab=pct)

        provider_ns_roots = parser.parse(dictConfig)
        for n,ns in enumerate(provider_ns_roots):
            log.debug("adding provider namespace root #{}: {}".format(n, ns))
            node._add_ns(ns)

        log.debug("Exiting")


    def init_sdk_namespace(self, node=None):
        """
        Description:
            Initialize SDK Namespace
        """
        log = LoggerAdapter(logger, {'name_ext': 'CushApplication.init_sdk_namespace'})
        log.debug("Entering")
        log.info('Initializing SDK namespace...')
        if node is None:
            node = self.sdk

        dictConfig = load_yaml_file(defaults.sdk_ns_file) 
        sdk_conf_parser = SdkConfigParser(provider_ns = self.provider,\
            nsroot=self.app_nsroot)
        sdk_ns_roots = sdk_conf_parser.parse(dictConfig)
        for ns in sdk_ns_roots:
            node._add_ns(ns)
        log.debug("Exiting")



    def init_ui_namespace(self):
        """
        Description:
            User Interface Namespace Initialization routine. Takes the SDK, Runtime and
            User Namespaces and puts them together to create the exposed UI Namespace
        """
        log = LoggerAdapter(logger, {'name_ext': 'CushApplication.init_ui_namespace'})
        log.debug("Entering")
        log.info("Initializing UI Namespace...")

        #- start with a copy of the SDK NS
        ui_ns = copy.deepcopy(self.sdks)
        ui_ns._nsid = 'ui'
        ui_ns._add_item('aws.users', self.user.aws._all())
        ui_ns._add_item('aws.ec2.regions', self.implementors.boto.aws.elb.regions)
        self.ui = ui_ns        
        self.app_nsroot._add_ns(self.ui)
        log.debug("Exiting")




def get_cush(name='default'):
    """
    Description:
        module-level convenience method to get an application object
    """
    return CushApplication(name=name)

