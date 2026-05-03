import io
import secrets
from base64 import b32encode, b64encode
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pyotp import TOTP
from pyotp.utils import build_uri
from qrcode import QRCode
from qrcode.image.svg import SvgPathImage

from global_config import AuthType, GlobalConfig
from helpers import get_env

from ..base import BaseAuth
from ..models import Login, Token

global_config = GlobalConfig()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token", auto_error=False)


class LocalAuth(BaseAuth):
    JWT_ALGORITHM = "HS256"

    def __init__(self) -> None:
        self.username = get_env("FLATNOTES_USERNAME", mandatory=True).lower()
        self.password = get_env("FLATNOTES_PASSWORD", mandatory=True)
        self.secret_key = get_env("FLATNOTES_SECRET_KEY", mandatory=True)
        self.session_expiry_days = get_env(
            "FLATNOTES_SESSION_EXPIRY_DAYS", default=30, cast_int=True
        )

        # TOTP
        self.is_totp_enabled = False
        if global_config.auth_type == AuthType.TOTP:
            self.is_totp_enabled = True
            self.totp_key = get_env("FLATNOTES_TOTP_KEY", mandatory=True)
            self.totp_key = b32encode(self.totp_key.encode("utf-8"))
            self.totp = TOTP(self.totp_key)
            self.last_used_totp = None
            self._display_totp_enrolment()

    def login(self, data: Login) -> Token:
        # Check Username
        username_correct = secrets.compare_digest(
            self.username.lower(), data.username.lower()
        )

        # Check Password & TOTP
        expected_password = self.password
        if self.is_totp_enabled:
            current_totp = self.totp.now()
            expected_password += current_totp
        password_correct = secrets.compare_digest(
            expected_password, data.password
        )

        # Raise error if incorrect
        if not (
            username_correct
            and password_correct
            # Prevent TOTP from being reused
            and (
                self.is_totp_enabled is False
                or current_totp != self.last_used_totp
            )
        ):
            raise ValueError("Incorrect login credentials.")
        if self.is_totp_enabled:
            self.last_used_totp = current_totp

        # Create Token
        access_token = self._create_access_token(data={"sub": self.username})
        return Token(access_token=access_token)

    def authenticate(
        self, request: Request, token: str = Depends(oauth2_scheme)
    ):
        # If no token in Authorization header, check cookies.
        # The frontend namespaces the cookie name by origin (e.g. "token_<base64>")
        # so multiple instances on different domains don't share session state.
        # We accept "token" (legacy) or any "token_*" cookie whose JWT is valid.
        if token is None:
            for name, value in request.cookies.items():
                if (name == "token" or name.startswith("token_")) and value:
                    try:
                        self._validate_token(value)
                        token = value
                        break
                    except Exception:
                        continue

        # Validate — raises 401 if still no valid token
        if not self._validate_token_bool(token):
            raise HTTPException(
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _validate_token(self, token: str) -> bool:
        """Validate token, raising JWTError or ValueError on failure."""
        if token is None:
            raise ValueError("No token")
        payload = jwt.decode(
            token, self.secret_key, algorithms=[self.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None or username.lower() != self.username:
            raise ValueError("Invalid subject")
        return True

    def _validate_token_bool(self, token: str) -> bool:
        """Validate token, returning False instead of raising."""
        try:
            return self._validate_token(token)
        except Exception:
            return False

    def _create_access_token(self, data: dict):
        to_encode = data.copy()
        expiry_datetime = datetime.utcnow() + timedelta(
            days=self.session_expiry_days
        )
        to_encode.update({"exp": expiry_datetime})
        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.JWT_ALGORITHM
        )
        return encoded_jwt

    def _display_totp_enrolment(self):
        # Fix for #237. Remove padding as per spec:
        # https://github.com/google/google-authenticator/wiki/Key-Uri-Format#secret
        unpadded_secret = self.totp_key.rstrip(b"=")
        uri = build_uri(unpadded_secret, self.username, issuer="flatnotes")
        qr = QRCode()
        qr.add_data(uri)
        print(
            "\nScan this QR code with your TOTP app of choice",
            "e.g. Authy or Google Authenticator:",
        )
        qr.print_ascii()
        print(
            f"Or manually enter this key: {self.totp.secret.decode('utf-8')}\n"
        )

    def get_totp_setup_data(self) -> dict:
        """Return TOTP enrolment data for the frontend modal.

        Returns a dict with:
          uri     — the otpauth:// URI
          secret  — the base32 manual-entry key
          svg     — inline SVG QR code (no Pillow required)
        """
        if not self.is_totp_enabled:
            return None

        unpadded_secret = self.totp_key.rstrip(b"=")
        uri = build_uri(unpadded_secret, self.username, issuer="flatnotes")
        secret_str = self.totp.secret.decode("utf-8")

        # SvgPathImage is bundled with qrcode — no Pillow dependency needed
        qr = QRCode(image_factory=SvgPathImage)
        qr.add_data(uri)
        qr.make(fit=True)
        svg_image = qr.make_image()
        buf = io.BytesIO()
        svg_image.save(buf)
        svg_str = buf.getvalue().decode("utf-8")

        return {
            "uri": uri,
            "secret": secret_str,
            "svg": svg_str,
        }