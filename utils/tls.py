from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates


def extract_pfx_to_pem(
    pfx_path: str,
    password: str,
    cert_out: str,
    key_out: str,
) -> tuple[str, str]:
    pfx_data = Path(pfx_path).read_bytes()

    private_key, certificate, _additional_certs = load_key_and_certificates(
        pfx_data,
        password.encode(),
    )

    if private_key is None or certificate is None:
        raise ValueError("Não foi possível extrair certificado/chave do PFX.")

    Path(cert_out).write_bytes(certificate.public_bytes(Encoding.PEM))

    Path(key_out).write_bytes(
        private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=NoEncryption(),
        )
    )

    return cert_out, key_out