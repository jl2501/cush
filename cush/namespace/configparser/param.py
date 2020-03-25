from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

from thewired import NamespaceConfigParser, ParametizedCall
from thewired import NamespaceConfigParsingError

class ParamConfigParser(NamespaceConfigParser):
    """
    Description:
        parse the parameters config file into ParametizedCall objects
    """
    def __init__(self, param_ns, nsroot=None, prefix=None):
        """
        Input:
            param_ns: parameter Namespace root
            nsroot: optional nsroot for symref lookups
        """
        self.param_ns = param_ns
        self.nsroot = nsroot
        self._param_marker = ParametizedCall._param_dict_mark_key
        super().__init__(prefix=prefix, nsroot=nsroot)


    def parse_submap(self, dictConfig, cur_ns, prev_ns=None):
        log = LoggerAdapter(logger, {'name_ext' : 'ParamConfigParser.parse_submap'})
        if self._param_marker in dictConfig.keys():
            log.debug("Found param marker...")
            param_d = {self._param_marker: dict(dictConfig[self._param_marker])}
            log.debug("Made param dict: {}".format(param_d))
            #- add raw dict
            if prev_ns:
                prev_ns._add_item(cur_ns._name, param_d, overwrite=True)
            else:
                msg = "Can't add params without parent node"
                raise NamespaceConfigParsingError(msg)
        else:
            log.debug("calling super().parse_submap...")
            super().parse_submap(dictConfig, cur_ns)
