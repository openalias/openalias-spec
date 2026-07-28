#!/usr/bin/env python3
"""
Resolve an OpenAlias and pay the highest-priority address this wallet supports.

Selects among the recipient's `_openalias-payment` records using the
DNSSEC-authenticated resolution in openalias.py, shows the recipient's display
name (from `_openalias-metadata`), and confirms the address before "sending".

Requires: dnspython with cryptography  ->  pip install "dnspython[dnssec]"

Usage:
    python3 python-wallet.py donate@openalias.org
"""

import sys

import openalias

# What this wallet can pay, as (network, asset) pairs:
#   ("net", None)  -> only the network's native asset
#   ("net", "sym") -> one specific asset on that network
#   ("net", "*")   -> any asset on that network (e.g. a wallet that accepts
#                     the native coin and every token on it)
SUPPORTED = {
    ("btc", None),    # native BTC only
    ("xmr", None),    # native XMR only
    ("eth", "*"),     # any asset on Ethereum (ETH and all tokens)
    ("trx", "usdt"),  # only USDT on Tron
}


def is_supported(record: openalias.PaymentRecord) -> bool:
    """True if this wallet can pay `record` (see SUPPORTED for the conventions)."""
    network = record.network
    if (network, "*") in SUPPORTED:  # the wallet accepts any asset on this network
        return True
    # Collapse a native-asset payment to None so it matches a ("net", None)
    # entry. Nativeness comes from the OA2 network list, so a native asset whose
    # id differs from the network code (e.g. eth on base) is still recognized.
    asset = None if openalias.is_native(record) else record.asset
    return (network, asset) in SUPPORTED


def main(alias: str) -> int:
    try:
        found = openalias.payments(alias)
    except openalias.NotAnAlias as exc:
        print(exc)
        return 1
    except openalias.InsecureLookup as exc:
        print(f"Refusing an unauthenticated result: {exc}")
        return 1
    except openalias.LookupFailed as exc:
        print(f"Lookup failed: {exc}")
        return 1

    if not found:
        print(f"No OpenAlias v2 payment records for {alias}.")
        return 1

    payable = [record for record in found if is_supported(record)]  # already priority-sorted
    if not payable:
        offered = ", ".join(sorted({record.network for record in found}))
        print(f"{alias} accepts {offered}; this wallet supports none of them.")
        return 1

    chosen = payable[0]

    # Metadata is optional and must never block a payment.
    name = None
    try:
        meta = openalias.metadata(alias)
        name = meta.get("name") if meta else None
    except openalias.OpenAliasError:
        pass

    print(f"Paying {name or alias}")
    print(f"  network:      {chosen.network}")
    if chosen.asset:
        print(f"  asset:        {chosen.asset}")
    if chosen.address_type:
        print(f"  address type: {chosen.address_type}")
    print(f"  address:      {chosen.address}")
    if chosen.amount is not None:
        print(f"  amount:       {chosen.amount} {chosen.effective_asset}")
    if chosen.memo:
        print(f"  memo:         {chosen.memo}")

    # Confirm the resolved address with the user before sending.
    if input("\nSend to this address? [y/N] ").strip().lower() == "y":
        print("... (the wallet would build and broadcast the transaction here)")
    else:
        print("Cancelled.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <alias>   e.g. donate@openalias.org")
    sys.exit(main(sys.argv[1]))
