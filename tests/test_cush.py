import pytest

import cush
from cush import __version__
from thewired import Namespace

def test_version():
    assert __version__ == '0.0.1'

def test_CushApplication_init():
    c = cush.CushApplication(name='test1', namespace=Namespace())
    assert c.name == 'test1'

def test_init_user():
    cushapp = cush.CushApplication(name='test2', namespace=Namespace())
    cushapp.init_user_namespace()

def test_init_cush():
    cush.init_cush(step=False)
    assert cush.get_cush().name == 'default'
