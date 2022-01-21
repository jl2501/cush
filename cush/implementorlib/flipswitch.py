from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

import collections
from typing import Union
from thewired import Namespace, NamespaceNodeBase, Nsid

#TODO: move Flipswitch to thewired; its wiring
class Flipswitch(NamespaceNodeBase):
    """
    Description:
        Set an implementor's state to be "on" / "off".
        When an implementor is used, this object should be looked up to find its on/off state.

        If cush's design thought that modifying implementor objects was a good idea,
        then this could just be an attribute on each implementor object that would say
        at runtime if it was "active" or not, and the code using it could care / not care about that,
        but would generally use that attribute to selectively skip making any actual call to any implmentor
        whose Flipswitch state is 'off'.

        One other thing this object does is allow one to chain flipswitches via its children attribute.
        Any time a flipswitch changes state through normal mechanisms, the state will be propagated to all the
        Flipswitches that are members of the `children` attribute

        (we don't want to modify implementor objects after they've been returned from the provisioner b/c we don't actually
         have any guarantee that these objects are mutable. Wrapping them is possible, but then that breaks the concept of the
         implementor namespace where you can have a single namespace of all the raw sdk objects with simple names, which by itself
         is pretty useful even w/out the rest of the configs that are possible to create the higher layer namespaces)
        
    """
    def __init__(self, state:str='on', *, nsid:Union[str, Nsid], namespace:Namespace):
        """
        Input:
            state: "on" or "off"
        """
        log = LoggerAdapter(logger, {'name_ext' : 'Flipswitch.__init__'})
        log.debug(f"entering: {nsid=} {namespace=}")
        super().__init__(nsid=nsid, namespace=namespace)
        self.children = list()    #- outputs from all implementor provisioners using this
        self._active_names = ['on', 'active', True]
        self._inactive_names = ['off', 'inactive', False]
        self.state = state
        log.debug("exiting")

    @property
    def state(self):
        """
        Description:
            simple interface for user readable state as a string
        """
        return self._state


    @state.setter
    def state(self, value):
        """
        Description:
            interface to setting state to a string
        """
        log = LoggerAdapter(logger, {'name_ext':'Flipswitch.state setter'})
        log.debug("Entering")
        log.debug("setting flipswitch state to <{}>".format(value))
        if isinstance(value, str):
            value = value.lower()
        else:
            log.warning("casting flipswitch state to boolean: {}".format(value))
            value = bool(value)

        if value in self._active_names:
            self._state = "on"
        elif value in self._inactive_names:
            self._state = "off"

        #- propagate to children
        for child in self.children:
            if isinstance(child, str):
                child_nsid = child
                #- treat as NSID
                #child = self.ns.flipswitch._lookup(child_nsid)
                child = self._ns.lookup('.flipswitch' + child_nsid)
            log.debug("Propagating state for child {}".format(child))
            child.state = self.state
        log.debug("Exiting")


    @property
    def _state(self):
        """
        Description:
            internal state that stringifies the internal _active boolean
        """
        if self._active is True:
            return "on"
        elif self._active is False:
            return "off"



    @_state.setter
    def _state(self, value):
        """
        Description:
            set internal state, making sure that internal active state is always a boolean
        """
        log = LoggerAdapter(logger, {'name_ext':'Flipswitch._state setter'})
        if value == "on":
            self._active = True
        elif value == "off":
            self._active = False
        else:
            #- TODO: use warnings.warn
            log.warning("Converting [{}] to boolean to set internal state".format(value))
            self._active = bool(value)
        

    def add_child(self, child):
        """
        Description:
            add an object to our internal list of children
        """
        log = LoggerAdapter(logger, {'name_ext' : 'Flipswitch.add_child'})
        log.debug("Entering")
        if isinstance(child, str):
            #- treat str as NSID
            self.children.append(child)
            log.debug("Exiting")
            return
        else:
            try:
                self.children.append(child.nsid)
                log.debug("Exiting")
                return
            except AttributeError as err:
                msg = "Can't get NSID from flipswitch child: {}".format(child)
                raise ValueError(msg) from err



    def add_children(self, children):
        log = LoggerAdapter(logger, {'name_ext' : 'Flipswitch.add_children'})
        log.debug("Entering")
        child_nsids = list()
        for child in children:
            if isinstance(child, str):
                #- treat strings as NSIDS
                child_nsids.append(child)
            else:
                try:
                    child_nsids.append(child.nsid)
                except AttributeError as err:
                    msg = "Can't get NSID for flipswitch child: {}".format(child)
                    raise ValueError(msg) from err

        self.children.extend(child_nsids)
        log.debug("Exiting")


    def flip(self):
        """
        Description:
            change the state of this node to the opposite of its current state.
            Then explicitly change the state of all children nodes to the final state
        """
        log = LoggerAdapter(logger, {'name_ext':'Flipswitch.flip'})
        log.debug("Entering")
        if self.state == 'on':
            self.state = 'off'
        else:
            self.state = 'on'
        log.debug("Exiting")


    def __str__(self):
        return "{}: <{}>".format(self.nsid, self.state)


    def __repr__(self):
        return "{}:{} : <{}>".format(self.__class__.__name__, self.nsid, self.state)


    def __bool__(self):
        """
        Description:
            shortcut to tell if a flipswitch is on or off
        Input:
            None
        Output:
            True if the flipswitch is 'on'
            False if it is 'off'
        """
        if self.state == 'on':
            return True
        elif self.state == 'off':
            return False
        else:
            raise ValueError("Flipswitch has unknown state: {}".format(self.state))
