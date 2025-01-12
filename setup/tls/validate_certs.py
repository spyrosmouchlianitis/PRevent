from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from pathlib import Path
import logging
from setup.tls.settings import CERT_PATH, KEY_PATH


def validate_certificates() -> bool:
    try:
        # Ensure file existence
        if not Path(CERT_PATH).is_file():
            logging.error(f"Certificate file not found: {CERT_PATH}")
            return False
        if not Path(KEY_PATH).is_file():
            logging.error(f"Private key file not found: {KEY_PATH}")
            return False
        
        # Load certificate
        with open(CERT_PATH, "rb") as cert_file:
            cert = x509.load_pem_x509_certificate(cert_file.read(), default_backend())
        
        # Load private key
        with open(KEY_PATH, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )
        
        # Verify public key matches private key
        if isinstance(private_key, rsa.RSAPrivateKey):
            public_key = private_key.public_key()
            if public_key.public_numbers() == cert.public_key().public_numbers():
                logging.info("Certificate and private key match.")
                return True
            else:
                logging.error("Public key and certificate mismatch.")
                return False
        else:
            logging.error("Unsupported private key type.")
            return False
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
    except ValueError as e:
        logging.error(f"Invalid file format: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    return False
