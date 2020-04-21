import pytest

import cush
from cush import __version__

def test_version():
    assert __version__ == '0.0.1'

@pytest.fixture
def cush_application():
    cush.init_cush(step=False)
    return cush.CushApplication()

def test_CushApplication(cush_application):
    assert cush_application.name == 'default'
