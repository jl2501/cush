import pytest

import cush
from cush import __version__
from thewired import Namespace

def test_CushApplication_init():
    c = cush.CushApplication(name='test1', namespace=Namespace())
    assert c.name == 'test1'



def test_init_userNS():
    cushapp = cush.CushApplication(name='init_user_test', namespace=Namespace())
    cushapp.init_user_namespace()
    assert cushapp.name == 'init_user_test'



#def test_init_implementorNS():
#    # ATM only default application name is supported for initializing implementor NS
#    #cushapp = cush.CushApplication(name='init_implementor_test', namespace=Namespace())
#    cushapp = cush.CushApplication(name='default', namespace=Namespace())
#    cushapp.init_user_namespace()
#    cushapp.init_implementor_namespace()
#    #assert cushapp.name == 'init_implementor_test'
#    assert cushapp.name == 'default'
#


#def test_init_defaultNS():
#    # ATM only default application name is supported for initializing implementor NS
#    #cushapp = cush.CushApplication(name='init_implementor_test', namespace=Namespace())
#    cushapp = cush.CushApplication(name='default', namespace=Namespace())
#    cushapp.init_user_namespace()
#    cushapp.init_implementor_namespace()
#    cushapp.init_default_namespace()
#    assert cushapp.name == 'default'

@pytest.fixture(scope="module")
def default_cush():
    cush.init_cush(step=False)
    return cush.get_cush()

def test_init_cush(default_cush):
    assert default_cush.name == 'default'

def test_provider_implementor_ns_get_root(default_cush):
    root_node = default_cush._ns.root
    provider_implementor_ns_root = root_node.provider.boto3.aws.s3.buckets.get._delegate.implementor_ns.get('.')
    assert str(provider_implementor_ns_root.nsid) == '.'
    assert str(provider_implementor_ns_root._delegate.nsid == '.implementor')
