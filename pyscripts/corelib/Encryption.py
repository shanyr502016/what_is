import base64
import hashlib

from Crypto.Cipher import AES
from Crypto import Random

from corelib.Loggable import Loggable

class Encryption(Loggable):
    
    def __init__(self):

        super().__init__(__name__)
        
        key = 'bgyu98&(*()U)YH(*YU)&)*(^^&*&BIJUHB'
        
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()
        
        
    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode())).decode("utf-8")

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
    
    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]