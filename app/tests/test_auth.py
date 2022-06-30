from test_main        import client, api_headers
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


## -- Test functions --

def test_get_token_wrong_all():
    response = client.post(url = '/token',
        headers = api_headers,
        json    = {
            "source_platform": "wrong-platform",
            "source_id":       "wrong-id"
        })
    assert response.status_code == HTTP_403_FORBIDDEN

def test_get_token_wrong_aud():
    response = client.post(url = '/token',
        headers = api_headers,
        json    = {
            "source_platform": "wrong-platform",
            "source_id":       "sample-id"
        })
    assert response.status_code == HTTP_403_FORBIDDEN

def test_get_token_wrong_sub():
    response = client.post(url = '/token',
        headers = api_headers,
        json    = {
            "source_platform": "sample-platform",
            "source_id":       "wrong-id"
        })
    assert response.status_code == HTTP_403_FORBIDDEN

# -- Test invalid auth

def test_get_list_no_auth():
    response = client.get(url = '/files/list',
        headers = api_headers,
        params  = {
            "subtitles": False,
            "hashes":    False
        })
    assert response.status_code == HTTP_403_FORBIDDEN

def test_get_list_wrong_auth():
    response = client.get(url = '/files/list',
        headers = api_headers | {
            "Authorization": "sample-token"
        },
        params  = {
            "subtitles": False,
            "hashes":    False
        })
    assert response.status_code == HTTP_403_FORBIDDEN

def test_get_list_wrong_token():
    response = client.get(url = '/files/list',
        headers = api_headers | {
            "Authorization": "Bearer sample-token"
        },
        params  = {
            "subtitles": False,
            "hashes":    False
        })
    assert response.status_code == HTTP_401_UNAUTHORIZED

# -- Get the correct API Token

def test_get_token_correct():
    response = client.post(url = '/token',
        headers = api_headers,
        json    = {
            "source_platform": "sample-platform",
            "source_id":       "sample-id"
        })
    assert response.status_code == HTTP_201_CREATED
    api_headers["Authorization"] = f'Bearer {response.json()["token"]}'