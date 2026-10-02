"""Make one HTTP request to a local app and check the response.

Usage:
  python3 http_check.py METHOD URL [--json JSON] [--expect-status N]
                        [--expect-body TEXT] [--timeout SECONDS] [--allow-remote]

Prints `STATUS <n>`, a `BODY` excerpt, and `PASS` or `FAIL <reason>`.
Exit 0: every expectation held. Exit 1: an expectation failed.
Exit 2: the request was refused or could not be made.

Without --expect-status, any 2xx status passes. Only http(s) URLs to loopback
hosts (localhost, 127.0.0.1, ::1) are allowed unless --allow-remote is given.
Environment proxy settings are ignored: this is for checking an app running on
the same machine.
"""
import argparse
import sys
import urllib.error
import urllib.parse
import urllib.request

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
BODY_EXCERPT_CHARS = 300


def send(method, url, json_body=None, timeout=10):
    """Return (status, body_text). HTTP error statuses are returned, not raised."""
    data = json_body.encode("utf-8") if json_body is not None else None
    request = urllib.request.Request(url, data=data, method=method.upper())
    if data is not None:
        request.add_header("Content-Type", "application/json")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        try:
            return error.code, error.read().decode("utf-8", "replace")
        finally:
            error.close()


def main(argv=None, stdout=None):
    out = stdout or sys.stdout
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("method")
    parser.add_argument("url")
    parser.add_argument("--json", dest="json_body", help="JSON request body")
    parser.add_argument("--expect-status", type=int)
    parser.add_argument("--expect-body", help="text the response body must contain")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--allow-remote", action="store_true", help="permit non-loopback hosts")
    args = parser.parse_args(argv)

    parsed = urllib.parse.urlparse(args.url)
    if parsed.scheme not in ("http", "https"):
        print(f"ERROR refused: only http(s) URLs are allowed, got {args.url!r}", file=out)
        return 2
    if not args.allow_remote and parsed.hostname not in LOOPBACK_HOSTS:
        print(f"ERROR refused: {parsed.hostname!r} is not a loopback host; pass --allow-remote to override", file=out)
        return 2

    try:
        status, body = send(args.method, args.url, args.json_body, args.timeout)
    except (urllib.error.URLError, OSError) as error:
        print(f"ERROR network: {error}", file=out)
        return 2

    print(f"STATUS {status}", file=out)
    print(f"BODY {body[:BODY_EXCERPT_CHARS]!r}", file=out)

    if args.expect_status is not None:
        if status != args.expect_status:
            print(f"FAIL status {status}, expected {args.expect_status}", file=out)
            return 1
    elif not 200 <= status < 300:
        print(f"FAIL status {status} is not 2xx", file=out)
        return 1
    if args.expect_body is not None and args.expect_body not in body:
        print(f"FAIL body does not contain {args.expect_body!r}", file=out)
        return 1
    print("PASS", file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
