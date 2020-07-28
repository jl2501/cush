"""
default values for things such as where to look up the rest of the configuration
information
"""

##########################################################################################
#                                                                                        #
#                            Config File Names                                           #
#                                                                                        #
##########################################################################################

config_dir = "~/.config/cush"
user_file = "user.yaml"
sdk_ns_file = "sdk_ns.yaml"
runtime_config_file = "config.yaml"
logging_config_file = "logging.yaml"
providers_ns_file = "provider.yaml"
params_ns_file = "parameters.yaml"
defaults_ns_file = "defaults.yaml"




##########################################################################################
#                                                                                        #
#                             Import Initialization Settings                             #
#                                 these settings affect cush/__init__.py                 #
##########################################################################################
#- moved into cush.__init__.py to make 'import cush' always work predictably (no side
#- effects from just importing cush)
#
# #- whether to step through interactively when initializing each namespace
# step_initialize = False
# #- the list of namespaces that will be initalized
# init_namespaces = ['user', 'implementor', 'default', 'param', 'provider', 'sdk']

