"""
Security Headers Middleware

Adds essential HTTP security headers to all responses to protect against common web vulnerabilities.

Security Headers Included:
- X-Content-Type-Options: Prevents MIME-sniffing attacks
- X-Frame-Options: Prevents clickjacking attacks
- X-XSS-Protection: Enables browser XSS filter (legacy browsers)
- Strict-Transport-Security (HSTS): Forces HTTPS connections
- Content-Security-Policy (CSP): Prevents XSS and data injection
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Controls browser features

Why these headers matter:
- Protect users from common attacks (XSS, clickjacking, MITM)
- Comply with security best practices (OWASP)
- Improve security score (Mozilla Observatory, Security Headers)
- Meet compliance requirements (PCI-DSS, HIPAA)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    This middleware implements OWASP security header recommendations
    to protect against common web vulnerabilities.

    Usage:
        from app.middleware.security_headers import SecurityHeadersMiddleware

        app.add_middleware(SecurityHeadersMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # X-Content-Type-Options: nosniff
        # Prevents browsers from MIME-sniffing responses
        # Protects against: Drive-by downloads, MIME confusion attacks
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: DENY
        # Prevents page from being loaded in frames/iframes
        # Protects against: Clickjacking attacks
        # Alternative: "SAMEORIGIN" if you need to frame your own pages
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: 1; mode=block
        # Enables browser's XSS filter (legacy, but still useful for old browsers)
        # Protects against: Cross-Site Scripting (XSS) attacks
        # Note: Modern browsers rely on CSP instead
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security (HSTS)
        # Forces browsers to use HTTPS for all future requests
        # Protects against: Man-in-the-Middle (MITM) attacks, SSL stripping
        # max-age=31536000: Enforce HTTPS for 1 year
        # includeSubDomains: Apply to all subdomains
        # preload: Allow inclusion in browser HSTS preload lists
        # NOTE: Only enable in production with HTTPS!
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content-Security-Policy (CSP)
        # Controls which resources browsers can load
        # Protects against: XSS, data injection, malicious scripts
        #
        # Policy breakdown:
        # - default-src 'self': Only load resources from same origin by default
        # - script-src 'self' 'unsafe-inline' cdn.jsdelivr.net: Allow same-origin scripts, inline scripts (for Swagger UI), and jsdelivr CDN
        #   ('unsafe-inline' needed for Swagger UI initialization)
        # - style-src 'self' 'unsafe-inline' cdn.jsdelivr.net: Allow same-origin styles, inline styles, and jsdelivr CDN (for Swagger UI)
        # - img-src 'self' data: https:: Allow images from same origin, data URLs, and HTTPS
        # - font-src 'self' data:: Allow fonts from same origin and data URLs
        # - connect-src 'self' cdn.jsdelivr.net: Only allow AJAX/WebSocket to same origin and jsdelivr CDN (for source maps)
        # - frame-ancestors 'none': Don't allow page to be framed (redundant with X-Frame-Options)
        # - base-uri 'self': Restrict <base> tag URLs
        # - form-action 'self': Only allow form submissions to same origin
        #
        # Note: cdn.jsdelivr.net is whitelisted for Swagger UI documentation
        # If you don't need Swagger UI in production, consider removing cdn.jsdelivr.net
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://cdn.jsdelivr.net; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # Referrer-Policy: strict-origin-when-cross-origin
        # Controls how much referrer information is sent
        # Protects against: Information leakage via referrer
        #
        # Policy: strict-origin-when-cross-origin
        # - Same origin: Send full URL
        # - Cross origin (HTTPS→HTTPS): Send origin only
        # - Cross origin (HTTPS→HTTP): Don't send referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features/APIs can be used
        # Protects against: Unauthorized access to device features
        #
        # Disabled features:
        # - geolocation: Location tracking
        # - microphone: Audio recording
        # - camera: Video recording
        # - payment: Payment Request API
        # - usb: USB device access
        # - magnetometer/gyroscope/accelerometer: Motion sensors
        #
        # Add features you need with =(self) or =(*)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        # Remove server header to avoid revealing server information
        # Protects against: Information disclosure, targeted attacks
        # Note: Uvicorn adds the server header after middleware runs,
        # so we override it with an empty value to effectively hide it
        response.headers["server"] = ""

        return response
