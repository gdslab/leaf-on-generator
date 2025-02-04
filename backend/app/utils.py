import base64
import os
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


def get_file_size_in_bytes(filepath: str) -> float:
    """Returns the size of the file at file_path in bytes.

    Args:
        filepath (str): The path to the file.

    Raises:
        FileNotFoundError: If the file does not exist.

    Returns:
        float: The size of the file in bytes.
    """

    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"The file '{filepath}' does not exist.")

    return os.path.getsize(filepath)
