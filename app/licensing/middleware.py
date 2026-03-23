"""License check middleware for Synco self-hosted deployments."""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.licensing.keys import validate_license_key

logger = logging.getLogger(__name__)

_SKIP_PATHS = {"/health", "/health/ready"}

_WARNING_BANNER = (
    '<div style="position:fixed;bottom:0;left:0;right:0;background:#dc2626;'
    "color:white;text-align:center;padding:12px;font-size:14px;z-index:9999;"
    '">'
    "\u26a0\ufe0f Invalid or missing license key. Please set SYNCO_LICENSE_KEY "
    'in your .env file. <a href="https://synco.app/pricing" '
    'style="color:#fef08a;text-decoration:underline;">Purchase a license</a>'
    "</div>"
)


class LicenseCheckMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, environment: str = "", license_key: str = "", license_secret: str = ""):
        super().__init__(app)
        self.is_self_hosted = environment == "self-hosted"
        self.license_valid = False
        if self.is_self_hosted:
            if license_key and license_secret:
                self.license_valid = validate_license_key(license_key, license_secret)
                if self.license_valid:
                    logger.info("License key validated successfully")
                else:
                    logger.warning("Invalid license key provided")
            else:
                logger.warning("Self-hosted mode: no license key configured")

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if not self.is_self_hosted or self.license_valid:
            return response

        if request.url.path in _SKIP_PATHS:
            return response

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                body += chunk.encode("utf-8")
            else:
                body += chunk

        body_text = body.decode("utf-8")
        if "</body>" in body_text:
            body_text = body_text.replace("</body>", f"{_WARNING_BANNER}</body>")

        from starlette.responses import Response

        return Response(
            content=body_text,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
