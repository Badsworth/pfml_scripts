#
# Logging of network connections.
#
# For outgoing connections, log these:
#
# - Before connecting, the IP addresses that the host name resolves to (names often resolve to a
#   different IP within AWS due to different DNS servers, geolocation, or VPC endpoints).
#
# - After successful connection:
#   - The actual IP address used.
#   - SSL certificate details (for security auditing or troubleshooting).
#

import socket

import requests.packages.urllib3.connection

import massgov.pfml.util.logging


def init():
    """Initialize network logging by patching calls."""
    (
        requests.packages.urllib3.connection.VerifiedHTTPSConnection.connect  # type: ignore[assignment]
    ) = patch_connect(requests.packages.urllib3.connection.VerifiedHTTPSConnection.connect)
    (
        requests.packages.urllib3.connection.HTTPConnection.connect  # type: ignore[assignment]
    ) = patch_connect(requests.packages.urllib3.connection.HTTPConnection.connect)


def patch_connect(original_connect):
    """Patch a connect method with additional logging."""

    def connect_log(self):
        logger = massgov.pfml.util.logging.get_logger(__name__)

        # Before connect: log IP addresses for the host name.
        addrs = socket.getaddrinfo(host=self.host, port=self.port, proto=socket.IPPROTO_TCP)
        logger.info("getaddrinfo %s:%s => %s", self.host, self.port, [addr[4] for addr in addrs])

        # Wrapped method call.
        original_connect(self)

        # After successful connect: log actual peer address and SSL certificate, if there is one.
        extra = {}

        if hasattr(self.sock, "getpeercert"):
            extra["cert"] = self.sock.getpeercert()

        if hasattr(self.sock, "getpeername"):
            extra["peername"] = self.sock.getpeername()

        logger.info("connected %s:%s", self.host, self.port, extra=extra)

    return connect_log
