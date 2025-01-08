import base64
import secrets


def generate_secret_key() -> str:
    """Creates secret key based on a random byte string with 64 bytes.

    Returns:
        str: Base64 encoded secret key converted to a string.
    """
    # Create random byte string with 64 bytes
    secret_key_bytes = secrets.token_bytes(64)

    # Base64 encode secret_key and convert to str object
    secret_key_str = base64.b64encode(secret_key_bytes).decode("utf-8")

    return secret_key_str
