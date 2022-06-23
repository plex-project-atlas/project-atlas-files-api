from   fastapi             import APIRouter, Path, Query
from   typing              import Any, List, Dict
from   libs.models         import FileList, MoveRequestList, MoveResponseList, RenameRequestList, RenameResponseList
from   starlette.requests  import Request


router = APIRouter()


@router.get(
    '/list',
    summary        = 'Returns a list of the video/subs files in the root directory',
    response_model = FileList
)
def list(
    request:           Request,
    subtitles: bool = Query(
        default     = False,
        title       = 'Subtitles',
        description = 'Specify whenever to include subtitles files or not'
    ),
    hashes:  bool = Query(
        default     = False,
        title       = 'Hashes',
        description = 'Specify whenever to calculate file hashes (Blake2S) or not'
    )
):
    """
    Search for all video/subtitles files in [FILES_DIR] and returns them as a list.
    """
    return request.state.files.get_list(include_subtitles = subtitles, calculate_hashes = hashes)


@router.patch(
    '/rename',
    summary        = 'Rename a list of files with optional checks (date, hash) without moving them',
    response_model = RenameResponseList
)
def rename(
    request: Request,
    renames: RenameRequestList
):
    """
    In-place renaming of a provided list of files with optional checks (date, hash).
    """
    return request.state.files.do_rename(renames.files)


@router.patch(
    '/move',
    summary        = 'Move a list of files with optional checks (date, hash) without renaming them',
    response_model = MoveResponseList
)
def move(
    request: Request,
    renames: MoveRequestList
):
    """
    In-place moving of a provided list of files with optional checks (date, hash).
    """
    return request.state.files.do_move(renames.files)
