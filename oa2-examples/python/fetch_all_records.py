#!/usr/bin/env python3
"""
Print every OpenAlias v2 record published for an alias.

Fetches and prints the `_openalias-payment` and `_openalias-metadata` records,
using the DNSSEC-authenticated resolution in openalias.py.

Requires: dnspython with cryptography  ->  pip install "dnspython[dnssec]"

Usage:
    python3 python-fetch-all-records.py donate@openalias.org
"""

import sys

import openalias


def main(alias: str) -> int:
    try:
        fqdn = openalias.normalize(alias)
    except openalias.NotAnAlias as exc:
        print(exc)
        return 1

    print(f"{alias}  ->  {fqdn}\n")

    exit_code = 0
    for prefix in (openalias.PAYMENT_PREFIX, openalias.METADATA_PREFIX):
        name = f"{prefix}.{fqdn}"
        try:
            found = openalias.records(alias, prefix)
        except openalias.InsecureLookup as exc:
            print(f"{name}: REFUSED — {exc}\n")
            exit_code = 1
            continue
        except openalias.LookupFailed as exc:
            print(f"{name}: lookup failed — {exc}\n")
            exit_code = 1
            continue

        if not found:
            print(f"{name}: no OpenAlias v2 records\n")
            continue

        print(f"{name}: {len(found)} record(s)")
        for fields in found:
            for key, value in fields.items():
                print(f"    {key} = {value}")
            print()

    return exit_code


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <alias>   e.g. donate@openalias.org")
    sys.exit(main(sys.argv[1]))
