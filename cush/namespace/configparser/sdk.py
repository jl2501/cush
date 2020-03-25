import collections
import cush.defaults as defaults
import thewired
from thewired import NamespaceNode
from thewired import NamespaceConfigParser

import logging
from logging import getLogger, LoggerAdapter

logger = getLogger(__name__)


class SdkConfigParser(NamespaceConfigParser):
    """
    Description:
        NamespaceConfigParser with a different method for parsing sub-keys.
        Specifically parses the SDK NS configuration and returns a root NamepsaceNode for
        each SDK that is specified, with NamespaceNodes using provider maps as specified
        in the configuration
    """
    def __init__(self, nsroot=None, provider_ns=None, prefix=None):
        """
        Input:
            dictConfig: the dictionary configuration
            implementor_ns: namespace of implementors to use when resolving references to
                implementor namespace ids in the dict config
            provider_tab: mapping of [provider class name] --> [provider class obejct]
        """
        super().__init__(prefix=prefix, nsroot=nsroot)
        self.provider_ns = provider_ns



    def parse_submap(self, mapping, cur_ns):
        """
        Description:
            override super class' method of this name to implement the provider class
            parsing and implementor parsing
        Input:
            mapping: dictConfig object
            cur_ns: current namespace node object to that we are descending from
        Output:
            None. Directly modifies the Root namespace nodes directly via _add_child()
        """
        log = LoggerAdapter(logger, {'name_ext' : 'SdkNsConfigParser.parse_submap'})
        log.debug('Entering with cur_ns: {}'.format(cur_ns))

        if cur_ns is None:
            log.error('Error parsing config: current namespace node is None.')
            raise ValueError('None is not a valid namespace object')

        log.debug('Iterating over keys: {}'.format(list(mapping.keys())))
        for key in mapping.keys():
            log.debug('----[cur_ns: {} | current key: {}'.format(cur_ns, key))

            if isinstance(mapping[key], collections.Mapping):
                log.debug('mapping[{}] is another mapping'.format(key))

                if 'provider' in mapping[key].keys():
                    log.debug('"provider" in mapping[{}].keys()'.format(key))
                    log.debug('mapping[{}].keys(): {}'.format(key, list(mapping[key].keys())))
                        
                    #- create a provided node
                    log.debug('creating provider map for: {}'.format(cur_ns._nsid))
                    provider_nsid = self.get_provider_nsid(mapping[key])
                    cur_ns._provider_map.set_provider_namespace(self.provider_ns)
                    cur_ns._provider_map.set_provider(key, provider_nsid)
                    #- only single provider

                else:
                    #- recursive case
                    cur_ns._add_child(key)
                    msg = 'recursing to parse dict config for key: [{}]'.format(key)
                    log.debug(msg)
                    self.parse_submap(mapping[key], getattr(cur_ns, key))

            else:
                #- leave it as a bare node
                msg = 'Setting immediate value for node {}.[{}]'.format(cur_ns._nsid, key)
                log.debug(msg)
                #setattr(cur_ns, key, mapping[key])
                cur_ns._add_item(key, mapping[key])

        log.debug('exiting: cur_ns: {}'.format(cur_ns))



    def get_provider_nsid(self, m):
        '''
        Description:
            helper method to create providers when at that section of the config

        Input:
            m: mapping/ dict-like object that specifies a provider
                Format:
                   m["provider"][provider_class_name] : { kwargs for provider class __init__}
        Output:
            the NSID of the provider
        '''
        log = LoggerAdapter(logger, {'name_ext' : 'SdkNsConfigParser.get_provider_nsid'})

        top_keys = list(m.keys())
        log.debug('making provider: {}'.format(top_keys))

        if len(top_keys) == 1 and top_keys[0] == 'provider':
            provider_nsid = m['provider']
            return provider_nsid

        else:
            msg = 'Malformed Provider Spec. More than one top-level "provider" key?'
            raise ValueError(msg)

