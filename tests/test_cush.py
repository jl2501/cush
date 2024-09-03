import pytest

import cush
from cush import __version__
from thewired import Namespace


@pytest.mark.parametrize('name', ['test1', 'test2'])
def test_CushApplication_name(name):
    c = cush.CushApplication(name=name, namespace=Namespace())
    assert c.name == name
    cush.CushApplication.del_application(name)

@pytest.mark.parametrize('CushApplication', ['init_user_test'], indirect=True)
def test_init_user_ns(CushApplication):
    CushApplication.init_user_namespace()
    assert CushApplication.name == 'init_user_test'

def test_init_implementor_ns(CushApplication):
    CushApplication.init_user_namespace()
    CushApplication.init_implementor_namespace()
    assert CushApplication.name == 'default'

def test_reinit_implementor_ns(CushApplication):
    CushApplication.init_user_namespace()
    CushApplication.init_implementor_namespace()
    assert CushApplication.name == 'default'

def test_init_default_ns(CushApplication):
    CushApplication.init_default_namespace()
    assert CushApplication.name == 'default'

def test_init_param_ns(CushApplication):
    CushApplication.init_param_namespace()
    assert CushApplication.name == 'default'

def test_init_provider_ns(CushApplication):
    CushApplication.init_provider_namespace()
    assert CushApplication.name == 'default'

def test_init_sdk_ns(CushApplication):
    CushApplication.init_provider_namespace()
    CushApplication.init_sdk_namespace()
    assert CushApplication.name == 'default'

def test_init_cush(CushApplication):
    cush.init_cush(step=False)

