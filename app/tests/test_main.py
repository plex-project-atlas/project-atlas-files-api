import pytest

from   main               import app
from   fastapi.testclient import TestClient
from   libs.files         import FileClient, get_api_settings

client       = TestClient(app)
api_headers  = {
    "Accept":       "application/json",
    "Content-Type": "application/json"
}

# -- Dependencies override --

app.state.file_client = FileClient()

## -- Test functions --

@pytest.mark.run(order = 1)
def test_get_api_settings():
    api_settings = get_api_settings()
    for _, value in api_settings.dict().items():
        assert value
