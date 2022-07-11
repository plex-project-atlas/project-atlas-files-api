from cmath import log
import logging
import jwt

from enum             import Enum
from fastapi          import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from libs.utils       import Settings, get_api_settings
from libs.models      import TokenRequest
from datetime         import datetime, timedelta, timezone
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_500_INTERNAL_SERVER_ERROR


class AuthErrorMessages(str, Enum):
    HTTP_401_INVALID_SCHEME      = "Invalid authentication scheme"
    HTTP_401_INVALID_CREDENTIALS = "Invalid credentials"
    HTTP_401_INVALID_TOKEN       = "Invalid or expired JWT token"
    HTTP_403_FORBIDDEN_SOURCE    = "Forbidden platform and/or source ID"
    HTTP_500_INVALID_PUBLIC_JWK  = "Missing public JWK key"
    HTTP_500_INVALID_PRIVATE_JWK = "Invalid private JWK key"
    HTTP_500_INVALID_ALGORITHM   = "Invalid JWT algorithm selected"

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error = auto_error)

    async def __call__(self, request: Request):
        api_settings: Settings = get_api_settings()
        credentials:  HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(status_code = HTTP_401_UNAUTHORIZED, detail = AuthErrorMessages.HTTP_401_INVALID_SCHEME)
            try:
                jwt.decode(
                    jwt        = credentials.credentials,
                    key        = api_settings.public_jwk,
                    algorithms = ["EdDSA"], # Ed448 - 224 bit security
                    options    = {
                        "verify_signature": True,
                        "require":          ["iss", "sub", "aud", "iat", "exp"],
                        "verify_iss":       True,
                        "verify_aud":       True,
                        "verify_iat":       True,
                        "verify_exp":       True,
                    },
                    audience = api_settings.allowed_aud,
                    issuer   = "project-atlas",
                    leeway   = 60
                )
            except jwt.exceptions.InvalidKeyError:
                raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = AuthErrorMessages.HTTP_500_INVALID_PUBLIC_JWK)
            except jwt.exceptions.InvalidAlgorithmError:
                raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = AuthErrorMessages.HTTP_500_INVALID_ALGORITHM)
            except (
                jwt.exceptions.InvalidTokenError, \
                jwt.exceptions.DecodeError, \
                jwt.exceptions.InvalidSignatureError, \
                jwt.exceptions.ExpiredSignatureError, \
                jwt.exceptions.InvalidAudienceError, \
                jwt.exceptions.InvalidIssuerError, \
                jwt.exceptions.InvalidIssuedAtError, \
                jwt.exceptions.ImmatureSignatureError, \
                jwt.exceptions.MissingRequiredClaimError
            ):
                raise HTTPException(status_code = HTTP_401_UNAUTHORIZED, detail = AuthErrorMessages.HTTP_401_INVALID_TOKEN)
            return credentials.credentials
        else:
            raise HTTPException(status_code = HTTP_401_UNAUTHORIZED, detail = AuthErrorMessages.HTTP_401_INVALID_CREDENTIALS)

def get_jwtoken( payload: TokenRequest, api_settings: Settings = get_api_settings() ) -> dict[str, str]:
    if payload.source_platform not in api_settings.allowed_aud or \
       payload.source_id       not in api_settings.allowed_sub:
        raise HTTPException(status_code = HTTP_403_FORBIDDEN, detail = AuthErrorMessages.HTTP_403_FORBIDDEN_SOURCE)
    try:
        utc_now = datetime.now(tz = timezone.utc)
        jwtoken = jwt.encode(
            payload   = {
                "iss": "project-atlas",
                "sub": payload.source_id,
                "aud": payload.source_platform,
                "iat": utc_now,
                "exp": utc_now + timedelta(hours = 1)
            },
            key       = api_settings.private_jwk,
            algorithm = "EdDSA" # Ed448 - 224 bit security
        )
    except jwt.exceptions.InvalidKeyError:
        raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = AuthErrorMessages.HTTP_500_INVALID_PRIVATE_JWK)
    except jwt.exceptions.InvalidAlgorithmError:
        raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = AuthErrorMessages.HTTP_500_INVALID_ALGORITHM)
    logging.info(f"[FilesAPI] - Issued API Token for: {payload.source_id}")
    return {"token": jwtoken}
