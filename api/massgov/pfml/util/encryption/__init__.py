import tempfile
from abc import ABC
from typing import Callable, Optional

import gnupg

import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)


class Crypt(ABC):
    def encrypt(self, str_val):
        pass

    def decrypt(self, bval):
        pass

    def set_on_data(self, on_data):
        pass

    def decrypt_stream(self, stream):
        pass

    def remove_keys(self):
        pass


class GpgCrypt(Crypt):
    def __init__(self, gpg_key, gpg_passphrase, recipient=None, homedir=None, on_data=None):
        """Set a different gnuhome so the key is not picked up by default in
        shared machine environments (i.e. on AWS)."""
        # if encrypting the same gpg directory used to generate a key needs to be passed in
        gpghome = homedir or tempfile.mkdtemp()
        gpg = gnupg.GPG(gnupghome=gpghome)
        gpg.encoding = "utf-8"
        gpg.on_data = on_data

        import_result = gpg.import_keys(gpg_key)

        if import_result.count == 0:
            logger.error("Failed to import GPG decryption key")
            raise ValueError(import_result.stderr)

        self.gpg = gpg
        self.passphrase = gpg_passphrase
        self.recipient = recipient
        self.gpg_key_fingerprints = import_result.fingerprints

    def set_on_data(self, on_data):
        self.gpg.on_data = on_data

    def decrypt(self, bval):
        result = self.gpg.decrypt(bval, passphrase=self.passphrase)

        if not result.ok:
            logger.error("Failed to decrypt file")
            raise ValueError(result.stderr)

        return result.data.decode("utf8")

    def decrypt_stream(self, stream):
        result = self.gpg.decrypt_file(stream, passphrase=self.passphrase)

        if not result.ok:
            logger.error("Failed to decrypt file")
            raise ValueError(result.stderr)

        return result.data

    def encrypt(self, str_val):
        return str(self.gpg.encrypt(str_val, self.recipient))

    def remove_keys(self):
        """Delete keys from the system to avoid any possibility of being viewed by
        other applications in a shared machine environment."""
        logger.info("Deleting GPG keys from system...")
        res = self.gpg.delete_keys(
            fingerprints=self.gpg_key_fingerprints, secret=True, passphrase=self.passphrase
        )
        if res.status != "ok":
            logger.warning("Failed to delete keys")
            logger.warning(res.stderr)


class Utf8Crypt(Crypt):
    on_data: Optional[Callable]

    def __init__(self):
        self.on_data = None

    def encrypt(self, str_val):
        return str_val.encode("utf8")

    def set_on_data(self, on_data):
        self.on_data = on_data

    def decrypt(self, bval):
        return bval.decode("utf8")

    def decrypt_stream(self, stream):
        if self.on_data is None:
            raise RuntimeError("set_on_data must be called before decrypt_stream")
        while data := stream.read(1000000):
            self.on_data(data)
        self.on_data("")

    def remove_keys(self):
        return
