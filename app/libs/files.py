import os
import magic
import shutil
import logging
import dateparser

from typing             import Tuple, List
from pydantic           import DirectoryPath, ByteSize
from pydantic.tools     import parse_obj_as
from libs.utils         import do_ops_preflight_checks, get_file_hash
from libs.models        import File, FileList, RenameRequest, RenameResponse, \
                               RenameResponseList, MoveRequest, MoveResponse, MoveResponseList
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


class FileClient:
    def __init__(self):
        self.block_size = parse_obj_as( ByteSize, os.environ.get('FILES_API_BLOCK_SIZE', '128 MiB') )
        logging.info(f'[FilesAPI] - Initializing block size to: {self.block_size.human_readable()}')
        self.files_dir = parse_obj_as( DirectoryPath, os.environ.get('FILES_API_FILES_DIR', '/files') )
        logging.info(f'[FilesAPI] - Initializing files directory to: {self.files_dir}')
        self.library_dir = parse_obj_as( DirectoryPath, os.environ.get('FILES_API_LIBRARY_DIR', '/library') )
        logging.info(f'[FilesAPI] - Initializing library directory to: {self.library_dir}')
        self.thread_count = int( os.environ.get( 'FILES_API_THREAD_COUNT', os.cpu_count() ) )
        if not self.thread_count:
            logging.warn('[FilesAPI] - Unable to detect CPU thread count')
            self.thread_count = 2
        logging.info(f'[FilesAPI] - Initializing operations thread count to: {self.thread_count}')

    def get_list(self, include_subtitles: bool = False, calculate_hashes: bool = False) -> FileList:
        fnames, files = [], []
        for (dir_path, _, file_names) in os.walk(self.files_dir):
            for file in file_names:
                fnames.append( os.path.join(dir_path, file) )

        for file in fnames:
            _, file_ext = os.path.splitext(file)
            file_mime   = None
            try:
                file_mime = magic.from_file(file, mime = True)
            except PermissionError as e:
                pass

            # Ref. https://support.plex.tv/articles/200471133-adding-local-subtitles-to-your-media/#toc-1
            if not ( ( file_mime and file_mime.startswith('video') ) or \
                (include_subtitles and file_ext and file_ext in ['.srt', '.smi', '.ssa', '.ass', '.vtt']) ):
                continue

            files.append( File(
                name      = os.path.basename(file),
                path      = os.path.dirname(file),
                size      = os.path.getsize(file),
                hash      = get_file_hash(file, self.block_size) if calculate_hashes else None,
                mod_date  = dateparser.parse( str( os.path.getmtime(file) ) ),
                mime_type = file_mime
            ) )

        return {"files": files}

    def do_rename(self, files: List[RenameRequest]) -> RenameResponseList:
        def chunk_rename(files: List[RenameRequest]) -> List[RenameResponse]:
            outcomes = []
            for file in files:
                src_file = f'{file.path}/{file.name}'
                dst_file = f'{file.path}/{file.new_name}'
                ops_precheck = do_ops_preflight_checks(file, self.block_size)
                if ops_precheck.result:
                    try:
                        os.rename(src_file, dst_file)
                    except (FileNotFoundError, PermissionError) as e:
                        ops_precheck.result = False,
                        ops_precheck.detail = f'{e.strerror}'
                        logging.warn(f'[FilesAPI] - Unable to rename "{src_file}" into "{dst_file}": {ops_precheck.detail}')

                outcomes.append( RenameResponse(
                    renamed = ops_precheck.result,
                    detail  = ops_precheck.detail,
                    **file.dict()
                ) )

            return outcomes

        chunksize = round(len(files) / self.thread_count) if (len(files) / self.thread_count) > 1 else 1
        with ThreadPoolExecutor(self.thread_count) as exe:
            rename_threads = [exe.submit(chunk_rename, files[i:(i + chunksize)]) for i in range(0, len(files), chunksize)]
            wait(rename_threads, return_when = ALL_COMPLETED)

        return {"files": [response for thread in rename_threads for response in thread.result()]}

    def do_move(self, files: List[MoveRequest]) -> MoveResponseList:
        outcomes = []
        for file in files:
            src_file = f'{file.path}/{file.name}'
            dst_file = f'{file.new_path}/{file.name}'
            ops_precheck = do_ops_preflight_checks(file, self.block_size)
            if ops_precheck.result:
                try:
                    shutil.move(src_file, dst_file)
                except (FileNotFoundError, PermissionError) as e:
                    ops_precheck.result = False
                    ops_precheck.detail = f'{e.strerror}'
                    logging.warn(f'[FilesAPI] - Unable to move "{src_file}" into "{file.new_path}": {ops_precheck.detail}')

            outcomes.append( MoveResponse(
                moved  = ops_precheck.result,
                detail = ops_precheck.detail,
                **file.dict()
            ) )

        return {"files": outcomes}
