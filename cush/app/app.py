import copy
import os

import thewired
from thewired import NamespaceNode, NamespaceConfigParser, NamespaceLookupError

from cush.util import ProviderClassTable
import cush.configuration as configuration
import cush.defaults as defaults
from cush.util import load_yaml_file
from cush.namespace import SdkConfigParser, UserConfigParser, ProviderConfigParser
from cush.namespace import ParamConfigParser
import cush.implementorlib as implementorlib
from cush.implementorlib.flipswitch import Flipswitch
import cush.implementor


from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)



class CushApplication(object):
    """
    Description:
        Container for the application state
    """
    #- app_name -> application instance mapping
    #- allows us to have multiple CushApplication objects at once
    #- each one will have its own setup if needed
    nsroot = NamespaceNode(namespace_id='.')
    nsroot._add_child('applications')
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



    def __new__(cls, name='default'):
        log = LoggerAdapter(logger, dict(name_ext='CushApplication.__new__'))
        try:
            app = cls._applications[name]
            log.debug("Found existing application named: {}".format(name))

        except (KeyError, NamespaceLookupError):
            log.debug("Creating new application object named: {}".format(name))
            app = super().__new__(cls)

        return app



    def __init__(self, name='default'):
        """
        Input:
            name: application object name
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
        self._nsid = self.nsroot._nsid + '.'.join(['applications', self.name])
        self.app_nsroot = NamespaceNode(\
            namespace_id='{}'.format(self._nsid), nsroot=self.nsroot,\
            is_nsroot=True)
        

        CushApplication._applications[self.name] = self
        CushApplication.nsroot.applications._set_item(self.name, self)

        #- flipswitches namespace
        self.flipswitch = NamespaceNode(\
            namespace_id = '.applications.{}.flipswitch'.format(self.name),\
            nsroot = self.app_nsroot)

        #- users namespace
        self.user = NamespaceNode(\
            namespace_id = '.applications.{}.user'.format(self.name),\
            nsroot = self.app_nsroot)

        #- initialized by _make_implementors
        #- implementors namespace
        self.implementor = NamespaceNode(\
            namespace_id = '.applications.{}.implementor'.format(self.name),
            nsroot = self.app_nsroot)

        #- implementor inputs namespace
        self.implementor_input = NamespaceNode(\
            namespace_id = '.applications.{}.implementor_input'.format(self.name),
            nsroot = self.app_nsroot)

        #- implementor provisioner namespace
        self.implementor_provisioner = NamespaceNode(\
            namespace_id = '.applications.{}.implementor_provisioner'.format(self.name),
            nsroot = self.app_nsroot)
        #- end of namespaces initialized by _make_implementors

        #- defaults namespace
        self.default = NamespaceNode(\
            namespace_id = '.applications.{}.default'.format(self.name),
            nsroot = self.app_nsroot)

        #- parameter namespace
        self.param = NamespaceNode(\
            namespace_id = '.applications.{}.param'.format(self.name),
            nsroot = self.app_nsroot)

        #- providers namespace
        self.provider = NamespaceNode(\
            namespace_id = '.applications.{}.provider'.format(self.name),
            nsroot = self.app_nsroot)

        #- sdk / primary logical overlay namespace
        self.sdk = NamespaceNode(\
            namespace_id = '.applications.{}.sdk'.format(self.name),
            nsroot = self.app_nsroot)

        #- ui / secondary logical overlay namespace
        self.ui = NamespaceNode(\
            namespace_id = '.applications.{}.ui'.format(self.name),
            nsroot = self.app_nsroot)

        log.debug('nsroot: {}'.format(self.nsroot))
        log.debug('****** finished initializing CushApplication')
        log.debug("Exiting")



    def init_user_namespace(self, node=None, flipswitch_root=None, overwrite=True):
        """
        Description:
            Initialize new style user namespace
        """
        log = LoggerAdapter(logger, {'name_ext' : 'CushApplication.init_user_namespace'})
        log.debug("Entering")
        log.info('Initializing user namespace...')
        if node is None:
            node = self.user
        user_ns_parser = UserConfigParser(nsroot=self.app_nsroot)
        dictConfig = load_yaml_file(defaults.user_file)
        user_ns = user_ns_parser.parse(dictConfig)
        log.debug("Got user namespace roots: {}".format(user_ns))

        if flipswitch_root is None:
            fs_root = self.flipswitch
        else:
            fs_root = flipswitch_root

        for root_node in user_ns:
            log.debug("adding '{}' to '{}'".format(root_node, node))
            node._add_ns(root_node, overwrite=overwrite)
        
            for nsid, user in root_node._list_leaves(nsids=True):
                fs = Flipswitch(nsid=nsid, nsroot=self.app_nsroot)
                self.flipswitch._add_item(nsid, fs)
        log.debug("Exiting")


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

