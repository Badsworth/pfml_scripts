import tempfile
from abc import ABC

import gnupg

import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)


class Crypt(ABC):
    def encrypt(self, str_val):
        pass

    def decrypt(self, bval):
        pass

    def decrypt_stream(self, stream):
        pass

    def remove_keys(self):
        pass


class GpgCrypt(Crypt):
    def __init__(self, gpg_key, gpg_passphrase, recipient=None, homedir=None):
        """Set a different gnuhome so the key is not picked up by default in
           shared machine environments (i.e. on AWS)."""
        # if encrypting the same gpg directory used to generate a key needs to be passed in
        gpghome = homedir or tempfile.mkdtemp()
        gpg = gnupg.GPG(gnupghome=gpghome)
        gpg.encoding = "utf-8"

        import_result = gpg.import_keys(gpg_key)

        if import_result.count == 0:
            logger.error("Failed to import GPG decryption key")
            raise ValueError(import_result.stderr)

        self.gpg = gpg
        self.passphrase = gpg_passphrase
        self.recipient = recipient
        self.gpg_key_fingerprints = import_result.fingerprints

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

        return result.data.decode("utf8")

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
            logger.warn("Failed to delete keys")
            logger.warn(res.stderr)


class Utf8Crypt(Crypt):
    def encrypt(self, str_val):
        return str_val.encode("utf8")

    def decrypt(self, bval):
        return bval.decode("utf8")

    def decrypt_stream(self, stream):
        return stream.read().decode("utf8")

    def remove_keys(self):
        return
