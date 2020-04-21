import pytest

from cush import __version__
def test_version():
    assert __version__ == '0.0.1'

import cush
def test_init_cush():
    cush.init_cush(step=False)
