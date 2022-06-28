import os
import pytest
import requests

from fastapi.testclient import TestClient
from app.main           import app
from app.libs.files     import FileClient
from app.libs.models    import FileList, RenameResponseList, MoveResponseList
from app.libs.utils     import ActionMessages
from routers.files      import get_file_client
from datetime           import datetime
from pathlib            import Path
from starlette.status   import HTTP_200_OK

client       = TestClient(app)
api_headers  = {
    "Accept":       "application/json",
    "Content-Type": "application/json"
}
sample_files = {
    "sample_3gp": {
        "source": "https://www.sample-videos.com/video123/3gp/144/big_buck_bunny_144p_1mb.3gp",
        "folder": "./",
        "hash":   "6343d456743bc30eaedc2886101328fc6667aa451a6ae3bf85a38bc5006ce2ca",
        "mime":   "video/3gpp"
    },
    "sample_mp4": {
        "source": "https://www.sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "folder": "./sample-dir1",
        "hash":   "0427bf0c8681a4058b1048c2cd64a2935d3b61827456f8455bcdd4495434b2e8",
        "mime":   "video/mp4"
    },
    "sample_srt": {
        "source": "https://filesamples.com/samples/document/txt/sample3.txt",
        "folder": "./sample-dir1",
        "hash":   "0020145b88a39fe2b5ddde2fb4e3e3d1a23b03b8def2eb33c01adf6c997f7d22",
        "mime":   "text/plain"
    },
    "sample_flv": {
        "source": "https://www.sample-videos.com/video123/flv/720/big_buck_bunny_720p_1mb.flv",
        "folder": "./sample-dir2",
        "hash":   "77e0baa1c181935838cad35d012ab42db07f809ecba233913f2b6de754e584e0",
        "mime":   "video/x-flv"
    },
    "sample_mkv": {
        "source": "https://www.sample-videos.com/video123/mkv/720/big_buck_bunny_720p_1mb.mkv",
        "folder": "./sample-dir1/sample-subdir1",
        "hash":   "76cbe8387ea81ea7b1159acb8b851e20244e4cfa4b232ada065ccb4a869fb857",
        "mime":   "video/x-matroska"
    }
}


# -- Dependencies override --

def get_test_file_client() -> FileClient:
    return FileClient()

app.dependency_overrides[get_file_client] = get_test_file_client

## -- Test functions --

@pytest.fixture(scope = "session")
def create_dummy_files_structure(tmp_path_factory: pytest.TempPathFactory):
    for key, val in sample_files.items():
        base_folder = os.path.normpath(val["folder"]).split(os.path.sep)[0]
        base_path   = os.path.normpath( os.path.join(tmp_path_factory.getbasetemp(), base_folder) )
        full_path   = os.path.normpath( os.path.join(tmp_path_factory.getbasetemp(), val["folder"]) )

        if not os.path.isdir(base_path):
            tmp_path_factory.mktemp(basename = base_folder, numbered = False)
        Path(full_path).mkdir(parents = True, exist_ok = True)

        download = requests.get(url = val["source"], timeout = 15)
        assert download.status_code == HTTP_200_OK
        file     = os.path.normpath( os.path.join(
            full_path, f'{key}.{key.split("_")[-1]}'
        ) )
        with open(file, 'wb') as f:
            f.write(download.content)

# -- /files/list --

def test_get_list_no_subs_no_hash(create_dummy_files_structure):
    response = client.get(url = '/files/list',
        headers = api_headers,
        params  = {
            "subtitles": False,
            "hashes":    False
        })
    assert response.status_code == HTTP_200_OK

    response = response.json()
    assert FileList(**response)

    subs_found = False
    hash_found = False
    for file in response["files"]:
        if file["name"].split('.')[-1] in ['srt', 'smi', 'ssa', 'ass', 'vtt']:
            subs_found = True
        if "hash" in file and file["hash"]:
            hash_found = True
        if subs_found and hash_found:
            break
    assert not subs_found
    assert not hash_found

def test_get_list_with_subs_and_hashes(create_dummy_files_structure):
    response = client.get(url = '/files/list',
        headers = api_headers,
        params  = {
            "subtitles": True,
            "hashes":    True
        })
    assert response.status_code == HTTP_200_OK

    response = response.json()
    assert FileList(**response)

    for k, v in sample_files.items():
        base_folder = os.environ.get("FILES_API_FILES_DIR", "")
        match_file  = next((
            file for file in response["files"] \
            if file["name"].startswith(k) and file["path"] == os.path.normpath(f'{base_folder}/{v["folder"]}')
        ), None)
        assert match_file
        assert match_file["size"]
        assert match_file["hash"] == v["hash"]
        assert match_file["mime_type"] == v["mime"]

# -- /files/rename --

def test_do_rename_wrong_name(create_dummy_files_structure):
    response = client.patch(url = '/files/rename',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_3gp.3gp",
                    "path":     "test-files",
                    "new_name": "sample_3gp.3gp"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert RenameResponseList(**response)

    assert bool(response["files"][0]["renamed"]) == False
    assert response["files"][0]["detail"] == ActionMessages.ERROR_SAME_NAME

def test_do_rename_wrong_size(create_dummy_files_structure):
    response = client.patch(url = '/files/rename',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_3gp.3gp",
                    "path":     "test-files",
                    "size":     8,
                    "new_name": "new_sample.3gp"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert RenameResponseList(**response)

    assert bool(response["files"][0]["renamed"]) == False
    assert ActionMessages.ERROR_SIZE_MISMATCH in response["files"][0]["detail"]

def test_do_rename_wrong_hash(create_dummy_files_structure):
    response = client.patch(url = '/files/rename',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_3gp.3gp",
                    "path":     "test-files",
                    "hash":     "my_wrong_hash",
                    "new_name": "new_sample.3gp"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert RenameResponseList(**response)

    assert bool(response["files"][0]["renamed"]) == False
    assert response["files"][0]["detail"] == ActionMessages.ERROR_HASH_MISMATCH

def test_do_rename_wrong_date(create_dummy_files_structure):
    response = client.patch(url = '/files/rename',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_3gp.3gp",
                    "path":     "test-files",
                    "mod_date": datetime.now().isoformat(),
                    "new_name": "new_sample.3gp"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert RenameResponseList(**response)

    assert bool(response["files"][0]["renamed"]) == False
    assert ActionMessages.ERROR_DATE_MISMATCH in response["files"][0]["detail"]

def test_do_rename_correct(create_dummy_files_structure):
    response = client.patch(url = '/files/rename',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_3gp.3gp",
                    "path":     "test-files",
                    "new_name": "new_sample.3gp"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert RenameResponseList(**response)

    assert bool(response["files"][0]["renamed"])

# -- /files/move --

def test_do_move_wrong_path(create_dummy_files_structure):
    response = client.patch(url = '/files/move',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_mkv.mkv",
                    "path":     "test-files/sample-dir1/sample-subdir1",
                    "new_path": "test-files/sample-dir1/sample-subdir1"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert MoveResponseList(**response)

    assert bool(response["files"][0]["moved"]) == False
    assert response["files"][0]["detail"] == ActionMessages.ERROR_SAME_PATH

def test_do_move_wrong_size(create_dummy_files_structure):
    response = client.patch(url = '/files/move',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_mkv.mkv",
                    "path":     "test-files/sample-dir1/sample-subdir1",
                    "size":     8,
                    "new_path": "test-files"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert MoveResponseList(**response)

    assert bool(response["files"][0]["moved"]) == False
    assert ActionMessages.ERROR_SIZE_MISMATCH in response["files"][0]["detail"]

def test_do_move_wrong_hash(create_dummy_files_structure):
    response = client.patch(url = '/files/move',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_mkv.mkv",
                    "path":     "test-files/sample-dir1/sample-subdir1",
                    "hash":     "my_wrong_hash",
                    "new_path": "test-files"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert MoveResponseList(**response)

    assert bool(response["files"][0]["moved"]) == False
    assert response["files"][0]["detail"] == ActionMessages.ERROR_HASH_MISMATCH

def test_do_move_wrong_date(create_dummy_files_structure):
    response = client.patch(url = '/files/move',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_mkv.mkv",
                    "path":     "test-files/sample-dir1/sample-subdir1",
                    "mod_date": datetime.now().isoformat(),
                    "new_path": "test-files"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert MoveResponseList(**response)

    assert bool(response["files"][0]["moved"]) == False
    assert ActionMessages.ERROR_DATE_MISMATCH in response["files"][0]["detail"]

def test_do_move_correct(create_dummy_files_structure):
    response = client.patch(url = '/files/move',
        headers = api_headers,
        json    = {
            "files": [
                {
                    "name":     "sample_mkv.mkv",
                    "path":     "test-files/sample-dir1/sample-subdir1",
                    "new_path": "test-files"
                }
            ]
        }
    )
    assert response.status_code == HTTP_200_OK
    response = response.json()
    assert MoveResponseList(**response)

    assert bool(response["files"][0]["moved"])
