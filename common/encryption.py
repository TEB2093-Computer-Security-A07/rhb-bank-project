import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key: str):
        self.block_size = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, decrypted_content: str) -> str:
        """Encrypts a string and returns Base64-encoded ciphertext."""
        content_padded = self._pad(decrypted_content)

        initialization_vector = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, initialization_vector)
        return base64.b64encode(
            initialization_vector + cipher.encrypt(content_padded.encode())
        ).decode()

    def decrypt(self, encrypted_content: str) -> str:
        """Decrypts a Base64-encoded ciphertext and returns the original string."""
        encrypted_content = base64.b64decode(encrypted_content)
        initialization_vector = encrypted_content[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, initialization_vector)

        decrypted_padded = cipher.decrypt(encrypted_content[AES.block_size:])
        return self._unpad(decrypted_padded).decode('utf-8')

    def _pad(self, content: str) -> str:
        """Applies PKCS7 padding to match AES block size."""
        return content + (self.block_size - len(content) % self.block_size) * chr(self.block_size - len(content) % self.block_size)

    @staticmethod
    def _unpad(content: str) -> str:
        """Removes PKCS7 padding."""
        return content[:-ord(content[len(content)-1:])]
