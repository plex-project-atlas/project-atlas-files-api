import os
import time
import logging
import warnings

from uvicorn            import Config, Server
from fastapi            import FastAPI, Request
from libs.logging       import LOG_LEVEL, setup_logging
from libs.files         import FileClient
from routers            import files
from starlette.status   import HTTP_200_OK


app = FastAPI(
    title        = 'Project: Atlas - Files Management API',
    description  = 'API used for bulk server-side file operations',
    version      = '0.0.1',
    docs_url     = '/',
    redoc_url    = None,
    debug        = True
)


# -- Main App --

@app.on_event('startup')
async def instantiate_clients():
    logging.info('[FilesAPI] - Initializing File client...')
    app.state.file_client = FileClient()

@app.middleware('http')
async def add_global_vars(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    logging.info(f'[FilesAPI] - The request was completed in: {(time.time() - start_time):.2f}s')
    return response


# import the /files branch of FilesAPI
app.include_router(
    files.router,
    prefix       = '/files',
    tags         = ['files'],
    responses = {
        HTTP_200_OK: {}
    }
)


if __name__ == '__main__':
    # WORKAROUND for https://github.com/scrapinghub/dateparser/issues/1013
    warnings.filterwarnings(
        "ignore",
        message = "The localize method is no longer necessary, as this time zone supports the fold attribute",
    )

    server = Server( Config(
        "main:app",
        host      = os.environ.get('UVICORN_HOST', '0.0.0.0'),
        port      = int( os.environ.get('UVICORN_PORT', '8080') ),
        factory   = True,
        workers   = 1,
        log_level = LOG_LEVEL,
    ) )

    # setup logging last, to make sure no library overwrites it
    # (they shouldn't, but it happens)
    setup_logging()

    server.run()
