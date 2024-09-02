import pytest

import cush
from thewired import Namespace

@pytest.fixture
def CushApplication(request):
    try:
        app_name = request.param
    except AttributeError:
        app_name = 'default'

    print(f"fixture creating {app_name}")
    c = cush.CushApplication(name=app_name, namespace=Namespace())
    yield c

    print(f"fixture deleting {app_name}")
    cush.CushApplication.del_application(app_name)
    del c
    print(f"len(cush.CushApplication._applications): {len(cush.CushApplication._applications)}")
