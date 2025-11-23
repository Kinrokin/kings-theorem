import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def generate_keypair(name, key_dir='keys'):
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()

    with open(f'{key_dir}/{name}.pem', 'wb') as f:
        f.write(priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(f'{key_dir}/{name}.pub', 'wb') as f:
        f.write(pub.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        ))

def verify_signature(pub_key_path, data: bytes, signature_b64: str) -> bool:
    try:
        with open(pub_key_path, 'rb') as f:
            pub_bytes = f.read()
            pub_key = serialization.load_ssh_public_key(pub_bytes)

        sig_bytes = base64.b64decode(signature_b64)
        pub_key.verify(sig_bytes, data)
        return True
    except Exception:
        return False
