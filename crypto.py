from bcrypt import hashpw, checkpw, gensalt
from pgpy import PGPKey, PGPUID, PGPSignature, PGPMessage
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
from pgpy.errors import PGPError
from pgpy.types import Fingerprint
import os
from constants import APP_VERSION, BRANCH_ID
from logging import info, error, warning

# TODO: All the PGP stuff is just ugly, should be a singleton class instead 

def pw_hash(pw: str) -> bytes:
    enc = pw.encode('utf-8')
    salt = gensalt()
    return hashpw(enc, salt)

def pw_check(pw1: str, pw2: bytes):
    if pw1 is None or pw2 is None:
            warning("Checking an empty password")
            return False
    enc = pw1.encode('utf-8')
    return checkpw(enc, pw2)

def generate_signing_keys() -> bool:
    key_path = os.path.join(os.getcwd(), 'data', 'crypto')
    if not os.path.exists(key_path):
        warning("Key directory does not exist, attempting to create it")
        try:
            os.makedirs(key_path, exist_ok=True)
        except Exception as e:
            error(f"Failed to create key directory ({str(e)})")
            return False
    pubkey_path = os.path.join(key_path, 'scuttle.pub.asc')
    privkey_path = os.path.join(key_path, 'scuttle.asc')
    if os.path.exists(privkey_path):
        try:
            key, _ = PGPKey.from_file(privkey_path)
            # Probably doesn't even delete it from memory but whatever
            del key
            info("Valid signing key is present")
            return True
        except (ValueError, PGPError) as e:
            error(f"Signing key is corrupted! ({str(e)})")
            return False    
    warning('Generating new signing keys')
    key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
    uid = PGPUID.new('SCUTTLE', f'SCUTTLE System version {APP_VERSION}; SCP-{BRANCH_ID}')
    key.add_uid(uid, usage={KeyFlags.Sign}, 
                hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512, HashAlgorithm.SHA224],
                ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
                compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP, CompressionAlgorithm.Uncompressed])
    try:
        with open(privkey_path, 'w') as keyfile:
            keyfile.write(str(key))
        with open(pubkey_path, 'w') as keyfile:
            keyfile.write(str(key.pubkey))
        info("Signing keys generated!")
        return True
    except Exception as e:
        error("Failed to export keys")
        return False
    
def load_key() -> PGPKey | None:
    key_path = os.path.join(os.getcwd(), 'data', 'crypto', 'scuttle.asc')
    if not os.path.exists(key_path):
        error("Error loading key: key doesn't exist")
        return
    try:
        key, _ = PGPKey.from_file(key_path)
    except (ValueError, PGPError) as e:
        error(f"Signing key is corrupted! ({str(e)})")
        return
    return key

def sign_file(file: str | bytes) -> PGPSignature | None:
    key = load_key()
    try:
        message = PGPMessage.new(file, file=True)
    except Exception as e:
        error(f'Error loading file {file} ({str(e)})')
        return
    signature = key.sign(message)
    return signature

def get_fingerprint() -> Fingerprint | None:
    key = load_key()
    return key.fingerprint