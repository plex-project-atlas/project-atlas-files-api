import os
import hashlib
import logging
import dateparser

from pydantic        import FilePath
from libs.models     import MoveRequest, RenameRequest, OpsPrefightCheckResult


def get_file_hash(file: FilePath, block_size: int) -> str | None:
    try:
        file_hash = None
        with open(file, "rb") as file:
            file_hash = hashlib.blake2s()
            while chunk := file.read(block_size):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except (FileNotFoundError, PermissionError) as e:
        return None

def do_ops_preflight_checks(file: RenameRequest | MoveRequest, block_size: int) -> OpsPrefightCheckResult:
    result   = OpsPrefightCheckResult(result = True)
    src_file = f'{file.path}/{file.name}'
    dst_file = f'{file.path}/{file.new_name}' \
               if isinstance(file, RenameRequest) else \
               f'{file.new_path}/{file.name}'

    if src_file == dst_file:
        result.result = False
        result.detail = f'Name has not changed, no rename needed' \
                        if isinstance(file, RenameRequest) else \
                        f'Path has not changed, no move required'
        logging.debug(f'[FilesAPI] - "{src_file}": {result.detail}')
    elif not ( file_hash := get_file_hash(src_file, block_size) ):
        result.result = False
        result.detail = f'Unable to access source file'
        logging.warn(f'[FilesAPI] - "{src_file}": {result.detail}')
    elif not ( ( file_size := os.path.getsize(src_file) ) == file.size ):
        result.result = False
        result.detail = f'Current file size does not match the provided one'
        logging.warn(f'[FilesAPI] - "{src_file}": {result.detail}')
    elif file.hash and file_hash != file.hash:
        result.result = False
        result.detail = f'Current file hash does not match the provided one'
        logging.warn(f'[FilesAPI] - "{src_file}": {result.detail}')
    elif file.mod_date and ( file_mod_date := dateparser.parse( str( os.path.getmtime(src_file) ) ) ) != file.mod_date:
        result.result = False
        result.detail = f'Current file modification date does not match the provided one (Delta: {file_mod_date - file.mod_date})'
        logging.warn(f'[FilesAPI] - "{src_file}": {result.detail}')

    return result
