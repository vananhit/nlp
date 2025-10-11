import pyotp
from backend.core.config import settings

class OTPManager:
    def __init__(self, secret_key: str):
        self.totp = pyotp.TOTP(secret_key)

    def verify(self, token: str) -> bool:
        """Verifies the TOTP token."""
        return self.totp.verify(token)

# Initialize the manager with the secret from settings
otp_manager = OTPManager(settings.TOTP_SECRET_KEY)
