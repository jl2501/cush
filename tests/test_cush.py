import pytest

import cush
from cush import __version__
from thewired import Namespace


@pytest.mark.parametrize('name', ['test1', 'test2'])
def test_CushApplication_name(name):
    c = cush.CushApplication(name=name, namespace=Namespace())
    assert c.name == name



def test_init_cush(CushApplication):
    cush.init_cush(step=False)

