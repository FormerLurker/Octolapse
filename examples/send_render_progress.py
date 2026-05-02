#!/usr/bin/env python3
"""
Example: send render progress updates to Octolapse from an external script.

Usage:
    python send_render_progress.py --host http://localhost:5000 --api-key YOUR_KEY --percent 42.5

This is useful for before/after render scripts configured in a camera profile that
do their own processing (e.g. re-encoding, watermarking) and want to drive the
Octolapse progress bar in the OctoPrint UI.
"""

import argparse
import sys
import time
import urllib.request
import urllib.error
import json


def send_progress(host, api_key, percent):
    """POST a progress update to Octolapse. Returns True on success."""
    url = "{}/plugin/octolapse/renderProgress".format(host.rstrip("/"))
    payload = json.dumps({"percent": percent}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if not body.get("success"):
                print("Octolapse returned an error: {}".format(body.get("error")), file=sys.stderr)
                return False
            return True
    except urllib.error.HTTPError as e:
        print("HTTP {}: {}".format(e.code, e.reason), file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print("Connection error: {}".format(e.reason), file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Send a render progress update to Octolapse.")
    parser.add_argument("--host", default="http://localhost:5000",
                        help="OctoPrint base URL (default: http://localhost:5000)")
    parser.add_argument("--api-key", required=True,
                        help="OctoPrint API key")
    parser.add_argument("--percent", type=float,
                        help="Progress percentage to send (0-100). "
                             "Omit to run a demo that counts from 0 to 100.")
    args = parser.parse_args()

    if args.percent is not None:
        # Single update mode
        ok = send_progress(args.host, args.api_key, args.percent)
        sys.exit(0 if ok else 1)
    else:
        # Demo mode: simulate progress from 0 to 100 over ~10 seconds
        print("Demo mode: sending progress 0→100 over 10 seconds")
        for i in range(101):
            percent = float(i)
            ok = send_progress(args.host, args.api_key, percent)
            status = "ok" if ok else "FAILED"
            print("  {:.1f}% [{}]".format(percent, status))
            if i < 100:
                time.sleep(0.1)
        print("Done.")


if __name__ == "__main__":
    main()
