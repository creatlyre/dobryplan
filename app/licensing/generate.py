"""Generate a Synco self-hosted license key.

Usage: python -m app.licensing.generate <secret>
"""

import sys

from app.licensing.keys import generate_license_key


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.licensing.generate <secret>")
        sys.exit(1)
    secret = sys.argv[1]
    key = generate_license_key(secret)
    print(f"License Key: {key}")


if __name__ == "__main__":
    main()
