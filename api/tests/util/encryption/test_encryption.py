import tempfile

import gnupg

from massgov.pfml.util.encryption import GpgCrypt, Utf8Crypt


def test_plain():
    crypt = Utf8Crypt()

    test_str = "This is a test!"
    encoded_str = crypt.encrypt(test_str)

    assert encoded_str == b"This is a test!"
    assert test_str == crypt.decrypt(encoded_str)


def test_gpg():
    tempdir = tempfile.mkdtemp()
    gpg = gnupg.GPG(gnupghome=tempdir)
    passphrase = "my passphrase"
    test_email = "testgpguser@mydomain.com"
    key_input_data = gpg.gen_key_input(name_email=test_email, passphrase=passphrase)
    key = gpg.gen_key(key_input_data)

    private_decryption_key = gpg.export_keys(
        keyids=key.fingerprint, secret=True, passphrase=passphrase
    )

    test_str = "This is a test!"

    crypt = GpgCrypt(private_decryption_key, passphrase, test_email, homedir=tempdir)
    encrypted_data = crypt.encrypt(test_str)

    decrypted_str = crypt.decrypt(encrypted_data)
    assert decrypted_str == test_str
