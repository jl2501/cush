import pytest

import cush
from thewired import Namespace

@pytest.fixture
def CushApplication(request):
    try:
        app_name = request.param
    except AttributeError:
        app_name = ''

    c = cush.CushApplication(name=app_name, namespace=Namespace())
    yield c
    c._applications.clear()
    del c

