from typing import NamedTuple

from OpenSSL import crypto


class X509CertAndKey(NamedTuple):
    cert: crypto.X509
    key: crypto.PKey


def generate_x509_cert_and_key(
    email_address: str = "email_address",
    common_name: str = "common_name",
    country_name: str = "NT",
    locality_name: str = "locality_name",
    state_or_province_name: str = "state_or_province_name",
    organization_name: str = "organization_name",
    organization_unit_name: str = "organization_unit_name",
    serial_number: int = 0,
    validity_start_in_seconds: int = 0,
    validity_end_in_seconds: int = 10 * 365 * 24 * 60 * 60,
) -> X509CertAndKey:
    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)

    # create a self-signed cert
    cert = crypto.X509()

    x509_name = cert.get_subject()
    x509_name.countryName = country_name
    x509_name.stateOrProvinceName = state_or_province_name
    x509_name.localityName = locality_name
    x509_name.organizationName = organization_name
    x509_name.organizationalUnitName = organization_unit_name
    x509_name.commonName = common_name
    x509_name.emailAddress = email_address
    cert.set_subject(x509_name)

    cert.set_serial_number(serial_number)
    cert.gmtime_adj_notBefore(validity_start_in_seconds)
    cert.gmtime_adj_notAfter(validity_end_in_seconds)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, "sha512")

    return X509CertAndKey(cert=cert, key=k)


def p12_encoded_cert(cert: X509CertAndKey) -> crypto.PKCS12:
    p12 = crypto.PKCS12()
    p12.set_privatekey(cert.key)
    p12.set_certificate(cert.cert)
    return p12


def write_x509_cert_key_pair(
    cert: X509CertAndKey, key_file: str = "private.key", cert_file: str = "selfsigned.crt"
) -> None:
    # can look at generated file using openssl:
    # openssl x509 -inform pem -in selfsigned.crt -noout -text
    with open(cert_file, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert.cert).decode("utf-8"))
    with open(key_file, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, cert.key).decode("utf-8"))
