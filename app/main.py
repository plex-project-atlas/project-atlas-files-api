import os
import time
import logging
import warnings

from uvicorn            import Config, Server
from fastapi            import FastAPI, Request, Depends
from routers            import files
from libs.logging       import LOG_LEVEL, setup_logging
from libs.files         import FileClient
from libs.security      import JWTBearer, get_jwtoken
from libs.models        import TokenRequest, TokenResponse
from starlette.status   import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


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

# JWT authentication
@app.post(
    path           = '/token',
    summary        = "New API Token",
    description    = "Request for a new JWT to authenticate API calls",
    response_model = TokenResponse,
    status_code    = HTTP_201_CREATED,
    responses      = {
        HTTP_403_FORBIDDEN: {"description": "Invalid requestor"}
    }
)
def get_token(request: TokenRequest):
    return get_jwtoken(request)

# import the /files branch of FilesAPI
app.include_router(
    files.router,
    prefix       = '/files',
    tags         = ['files'],
    dependencies = [Depends( JWTBearer() )],
    responses = {
        HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        HTTP_403_FORBIDDEN:    {"description": "Unauthenticated"}
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
        factory   = False,
        workers   = 1,
        log_level = LOG_LEVEL,
    ) )

    # setup logging last, to make sure no library overwrites it
    # (they shouldn't, but it happens)
    setup_logging()

    server.run()
