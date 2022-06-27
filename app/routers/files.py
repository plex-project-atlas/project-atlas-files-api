from libs.files         import FileClient
from fastapi            import APIRouter, Request, Query, Depends
from libs.models        import FileList, MoveRequestList, MoveResponseList, RenameRequestList, RenameResponseList


router = APIRouter()


# -- Singleton Services --

def get_file_client(request: Request) -> FileClient:
    return request.app.state.file_client

# -- Router paths

@router.get(
    '/list',
    summary        = 'Returns a list of the video/subs files in the root directory',
    response_model = FileList
)
def get_list(
    subtitles: bool = Query(
        default     = False,
        title       = 'Subtitles',
        description = 'Specify whenever to include subtitles files or not'
    ),
    hashes:    bool = Query(
        default     = False,
        title       = 'Hashes',
        description = 'Specify whenever to calculate file hashes (Blake2S) or not'
    ),
    file_client: FileClient = Depends(get_file_client)
) -> FileList:
    """
    Search for all video/subtitles files in [FILES_DIR] and returns them as a list.
    """
    return file_client.get_list(include_subtitles = subtitles, calculate_hashes = hashes)


@router.patch(
    '/rename',
    summary        = 'Rename a list of files with optional checks (date, hash) without moving them',
    response_model = RenameResponseList
)
def do_rename(
    renames:     RenameRequestList,
    file_client: FileClient = Depends(get_file_client)
) -> RenameResponseList:
    """
    In-place renaming of a provided list of files with optional checks (date, hash).
    """
    return file_client.do_rename(renames.files)


@router.patch(
    '/move',
    summary        = 'Move a list of files with optional checks (date, hash) without renaming them',
    response_model = MoveResponseList
)
def do_move(
    renames:     MoveRequestList,
    file_client: FileClient = Depends(get_file_client)
) -> MoveResponseList:
    """
    In-place moving of a provided list of files with optional checks (date, hash).
    """
    return file_client.do_move(renames.files)
