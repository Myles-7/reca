"""Exercise a temporary private MinIO object without business-model coupling."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import sys
import urllib.error
import urllib.request
from typing import cast

from app.core.config import settings

PAYLOAD = b"reca-m0-private-object"


def signed_request(method: str, path: str, body: bytes = b"") -> bytes:
    endpoint = str(settings.MINIO_ENDPOINT).rstrip("/")
    now = dt.datetime.now(dt.UTC)
    timestamp, day = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body).hexdigest()
    host = endpoint.removeprefix("http://").removeprefix("https://")
    headers = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": timestamp,
    }
    signed_headers = ";".join(headers)
    canonical_headers = "".join(f"{key}:{headers[key]}\n" for key in headers)
    canonical_request = (
        f"{method}\n{path}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )
    scope = f"{day}/us-east-1/s3/aws4_request"
    signing_key = hmac.new(
        ("AWS4" + settings.MINIO_ROOT_PASSWORD.get_secret_value()).encode(),
        day.encode(),
        hashlib.sha256,
    ).digest()
    for component in ("us-east-1", "s3", "aws4_request"):
        signing_key = hmac.new(signing_key, component.encode(), hashlib.sha256).digest()
    signature = hmac.new(
        signing_key,
        f"AWS4-HMAC-SHA256\n{timestamp}\n{scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}".encode(),
        hashlib.sha256,
    ).hexdigest()
    headers["Authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={settings.MINIO_ROOT_USER}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    request = urllib.request.Request(
        endpoint + path, data=body or None, method=method, headers=headers
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return cast(bytes, response.read())


def anonymous_denied(path: str) -> bool:
    endpoint = str(settings.MINIO_ENDPOINT).rstrip("/")
    try:
        with urllib.request.urlopen(endpoint + path, timeout=10) as response:
            return cast(bytes, response.read()) != PAYLOAD
    except urllib.error.HTTPError as error:
        return error.code in {401, 403, 404}
    except urllib.error.URLError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--object-key", default="m0-private.txt")
    parser.add_argument("--verify-anonymous-denial", action="store_true")
    parser.add_argument("--verify-persistence", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    object_path = f"/{args.bucket}/{args.object_key}"
    try:
        if not args.verify_persistence and not args.cleanup:
            signed_request("PUT", f"/{args.bucket}")
            signed_request("PUT", object_path, PAYLOAD)
        content = signed_request("GET", object_path)
        if hashlib.sha256(content).digest() != hashlib.sha256(PAYLOAD).digest():
            raise RuntimeError("authenticated object content hash mismatch")
        if args.verify_anonymous_denial and not anonymous_denied(object_path):
            raise RuntimeError("anonymous object access was not denied")
        if args.cleanup:
            signed_request("DELETE", object_path)
            signed_request("DELETE", f"/{args.bucket}")
    except Exception as error:
        print(f"MinIO smoke failed: {type(error).__name__}", file=sys.stderr)  # noqa: T201
        return 1
    print("MinIO private-object smoke passed")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
