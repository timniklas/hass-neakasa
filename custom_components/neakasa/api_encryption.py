from Cryptodome.Cipher import AES
from base64 import b64encode, b64decode
import time

from .const import AES_KEY_DEFAULT, AES_IV_DEFAULT

class APIEncryption:
    def __init__(self):
        self.resetEncryption()

    def resetEncryption(self):
        self.aes_key = self.AES_KEY_DEFAULT
        self.aes_iv = self.AES_IV_DEFAULT

    async def _pad(self, data):
        """NoPadding-compatible: manually fill up to block size 16 with zero bytes"""
        block_size = 16
        pad_len = block_size - (len(data) % block_size)
        return data + b'\x00' * pad_len if pad_len != 0 else data

    async def _unpad(self, data):
        """Removes null bytes at the end - not entirely safe, but how NoPadding texts are often handled"""
        return data.rstrip(b'\x00')

    async def encrypt(self, plain_text):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        padded = await self._pad(plain_text.encode('utf-8'))
        encrypted = cipher.encrypt(padded)
        return b64encode(encrypted).decode('utf-8')

    async def decrypt(self, encrypted_text):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        raw = b64decode(encrypted_text.replace(" ", "+"))
        decrypted = cipher.decrypt(raw)
        return (await self._unpad(decrypted)).decode('utf-8')

    async def _get_timestamp(self):
        return format(time.time(), '.6f')  # Seconds with 6 decimal places

    async def getToken(self):
        return await self.encrypt(self._token + '@' + await self._get_timestamp())

    async def decodeLoginToken(self, login_token):
        self.resetEncryption()

        decrypted = await self.decrypt(login_token)
        parts = decrypted.split('@')

        if len(parts) >= 1:
            self._token = parts[0]
        if len(parts) >= 2:
            self.userid = parts[1]
            self.uid = await self.encrypt(parts[1])
        if len(parts) >= 3:
            self.aes_key = parts[2].encode()
        if len(parts) >= 4:
            self.aes_iv = parts[3].encode()
