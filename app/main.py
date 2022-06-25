import os
import time
import logging
import warnings

from uvicorn            import Config, Server
from fastapi            import FastAPI
from functools          import lru_cache
from libs.logging       import LOG_LEVEL, setup_logging
from libs.files         import FileClient
from libs.utils         import Settings
from routers            import files
from starlette.requests import Request
from starlette.status   import HTTP_200_OK, \
                               HTTP_511_NETWORK_AUTHENTICATION_REQUIRED


clients = {}

@lru_cache()
def get_api_settings() -> Settings:
    return Settings()


app = FastAPI(
    title        = 'Project: Atlas - Files Management API',
    description  = 'API used for bulk server-side file operations',
    version      = '0.0.1',
    docs_url     = '/',
    redoc_url    = None,
    debug        = True
)


@app.on_event('startup')
async def instantiate_clients( api_settings: Settings = get_api_settings() ):
    logging.info('[FilesAPI] - Initializing File client...')
    clients['files']  = FileClient(api_settings)

@app.middleware('http')
async def add_global_vars(request: Request, call_next):
    request.state.files = clients['files']

    start_time = time.time()
    response = await call_next(request)
    logging.info( '[FilesAPI] - The request was completed in: %ss', '{:.2f}'.format(time.time() - start_time) )
    return response


# import the /files branch of FilesAPI
app.include_router(
    files.router,
    prefix    = '/files',
    tags      = ['files'],
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
        log_level = LOG_LEVEL,
    ) )

    # setup logging last, to make sure no library overwrites it
    # (they shouldn't, but it happens)
    setup_logging()

    server.run()
