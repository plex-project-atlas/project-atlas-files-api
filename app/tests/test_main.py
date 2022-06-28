import os
import pytest

from   app.libs.files import get_api_settings


## -- Test functions --

@pytest.mark.run(order = 1)
def test_get_api_settings():
    api_settings  = get_api_settings()
    assert api_settings.block_size
    assert os.path.normpath(api_settings.files_dir) == os.path.normpath('./test-files/')
