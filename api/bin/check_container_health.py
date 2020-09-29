#!/usr/bin/env python3

import argparse
import http.client


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-e", "--endpoint", default="http://localhost:1550", help="Container health status endpoint"
    )
    return vars(ap.parse_args())


def main():
    args = parse_args()
    endpoint = args["endpoint"]
    host_info = endpoint.split(":")
    port = int(host_info.pop())
    host = host_info[1].replace("//", "")
    conn = http.client.HTTPConnection(host, port)
    try:
        conn.request("GET", "/v1/status")
        resp = conn.getresponse()
        print(resp.status)
    except Exception:
        print(0)


if __name__ == "__main__":
    main()
