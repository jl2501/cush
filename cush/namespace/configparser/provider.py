from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

import collections
import operator

from thewired import NamespaceConfigParser

class ProviderConfigParser(NamespaceConfigParser):
    """
    Description:
        parse the configuration of providers into a namespace
    """
    def __init__(self, implementor_ns, implementor_state_ns, provider_ns,\
          provider_cls_tab, nsroot=None, prefix=None):
        """
        Input:
            implementor_ns: Implementor Namespace
            implementor_state_ns: Implementor State Namespace
            provider_ns: Provider Namespace
            provider_cls_tab: (value-result argument) dict that will be initialized to map
                available provider names to class objects
            prefix: NSID prefix for everything we put into the provider namespace
        """
        super().__init__(prefix=prefix, nsroot=nsroot)
        self.implementor_ns = implementor_ns
        self.implementor_state_ns = implementor_state_ns
        self.provider_ns = provider_ns
        self.provider_cls_tab = provider_cls_tab
        self.provider_names = self.provider_cls_tab.keys()
        self.nsroot = nsroot


    def parse_submap(self, mapping, cur_ns):
        """
        Description:
            override NamespaceConfigParser's parse_submap to begin looking for
            provider-specific stanzas and instantiating the providers in the provider
            namespace with their specified namespace id

        Input:
            mapping: dictConfig. (parsed YAML)
            cur_ns: current NamespaceNode

        Output:
            None: directly modifies the provider namespace
        """

        log = LoggerAdapter(logger, {'name_ext' : 'ProviderNsConfigParser.parse_submap'})
        log.debug('Entering with cur_ns: {}'.format(cur_ns))

        if cur_ns is None:
            log.error('Error parsing config: current namespace node is None.')
            raise ValueError('None is not a valid namespace object')

        log.debug('Iterating over keys: {}'.format(list(mapping.keys())))
        for key in mapping.keys():
            log.debug('----[cur_ns: {} | current key: {}'.format(cur_ns, key))

            if isinstance(mapping[key], collections.Mapping):
                log.debug('mapping[{}] is another mapping'.format(key))

                next_keys = list(mapping[key].keys())
                if len(next_keys) == 1 and next_keys[0] in self.provider_names:
                    log.debug('"provider" class found in mapping[{}].keys()'.format(key))
                    log.debug('mapping[{}].keys(): {}'.format(key, list(mapping[key].keys())))

                    #- only one provider name per line
                    provider_name = next_keys[0]
                    provider_instance = self._make_provider_from_dictConfig(mapping[key])
                    implementor_nsid = mapping[key][provider_name]['implementor']

                    log.debug("adding item: {} + {}".format(cur_ns, key))
                    cur_ns._add_item(key, provider_instance)

                else:
                    #- recursive case
                    cur_ns._add_child(key)
                    msg = 'recursing to parse dict config for key: [{}]'.format(key)
                    log.debug(msg)
                    self.parse_submap(mapping[key], getattr(cur_ns, key))

            else:
                #- leave it as a bare node
                msg = 'Setting immediate value for node {}.[{}]'.format(cur_ns._nsid, key)
                log.warning("Should never get here when parsing provider NS spec.")
                log.debug(msg)
                cur_ns._add_item(key, mapping[key])

        log.debug('exiting: cur_ns: {}'.format(cur_ns))




    def _make_provider_from_dictConfig(self, m):
        '''
        Description:
            helper method to create providers when at that section of the config

        Input:
            m: mapping/ dict-like object that specifies a provider
                Format:
                   m["provider"][provider_class_name] : { kwargs for provider class __init__}
        Output:
            an instantiated provider object
        '''
        log = LoggerAdapter(logger, {'name_ext' : 'ProviderNsConfigParser._make_provider_from_dictConfig'})

        top_keys = list(m.keys())
        provider_cls_names = self.provider_cls_tab.keys()

        log.debug('making provider: {}'.format(top_keys))

        if len(top_keys) == 1 and top_keys[0] in provider_cls_names:
            provider_name = top_keys[0]
            try:
                p_cls = self.provider_cls_tab[provider_name]

                #- TODO: move this to Provider-Specific parse code
                try:
                    #- replace formatter string with formatter object
                    eval_context = m[provider_name]['formatter']
                    nolocals = dict()
                    onlybuiltins = dict()
                    formatter = eval(eval_context, onlybuiltins, nolocals)
                    m[provider_name]['formatter'] = formatter

                except NameError:
                    msg = 'No such formatter available: {}'.format(eval_context)
                    raise ValueError(msg)

                #- create provider
                args_d = dict(m[provider_name])
                provider = p_cls(**args_d,\
                    implementor_namespace=self.implementor_ns,\
                    implementor_state_namespace=self.implementor_state_ns,\
                    nsroot=self.nsroot)
                return provider

            except AttributeError as err:
                msg = 'Malformed Provider Spec. Provider config should be a dict'
                log.debug('AttributeError: {}'.format(err))
                raise ValueError(msg) from err

            except KeyError as err:
                reason = 'not found in class table'
                log.debug('KeyError: {}'.format(err))
                log.error('Unable to instantiate provider: {} -{}'.format(\
                    provider_class_name, reason))

        else:
            msg = "Malformed Provider Spec. "
            msg += "Provider level key must be the name of a provider class"
            raise ValueError(msg)
