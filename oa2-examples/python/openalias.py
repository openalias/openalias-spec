"""
openalias — resolve OpenAlias v2 records.

A small, readable library for looking up OpenAlias v2 aliases (see the OA2
specification). It resolves aliases with local DNSSEC validation (see
dnssec.py) and parses records according to the OA2 "Key-Value Encoding" rules.

Trust model
-----------
DNS answers are validated locally: every signature is verified in-process, up a
chain of trust anchored at the DNS root (see dnssec.py), so the resolver used to
fetch the records does not have to be trusted. An answer that cannot be
validated is rejected (fail closed).

Requires: dnspython with cryptography  ->  pip install "dnspython[dnssec]"
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

import dnssec

__all__ = [
    "PaymentRecord",
    "payments",
    "metadata",
    "records",
    "normalize",
    "parse_record",
    "native_asset",
    "is_native",
    "OpenAliasError",
    "NotAnAlias",
    "InsecureLookup",
    "LookupFailed",
    "PAYMENT_PREFIX",
    "METADATA_PREFIX",
]

# --- configuration -----------------------------------------------------------

PAYMENT_PREFIX = "_openalias-payment"
METADATA_PREFIX = "_openalias-metadata"

# The OA2 network list, used to resolve each network's native asset. Defaults to
# the copy shipped alongside these examples; reassign to point elsewhere.
NETWORK_LIST_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "oa2-lists", "network.csv"
)

_KEY_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")


# --- errors ------------------------------------------------------------------

class OpenAliasError(Exception):
    """Base class for OpenAlias resolution errors."""


class NotAnAlias(OpenAliasError):
    """The input is a raw address, not an OpenAlias."""


class InsecureLookup(OpenAliasError):
    """The answer could not be DNSSEC-validated and must not be trusted."""


class LookupFailed(OpenAliasError):
    """The DNS lookup itself failed (network error, SERVFAIL, timeout, ...)."""


# --- alias normalization -----------------------------------------------------

def _to_ascii(domain: str) -> str:
    """Return `domain` with any internationalized labels as A-labels (Punycode)."""
    labels = []
    for label in domain.split("."):
        if label and not label.isascii():
            try:
                label = label.encode("idna").decode("ascii")
            except UnicodeError as exc:
                raise OpenAliasError(f"invalid domain label {label!r}: {exc}") from exc
        labels.append(label)
    return ".".join(labels)


def normalize(alias: str) -> str:
    """Turn user input into the FQDN to query, applying the OA2 input rules.

    An email-style '@' becomes '.', input without a '.' is treated as a raw
    address (`NotAnAlias`), and internationalized names are converted to
    A-labels. Also enforces DNS length limits.
    """
    alias = alias.strip().rstrip(".")
    if not alias:
        raise NotAnAlias("empty input")
    if alias.count("@") > 1:
        raise OpenAliasError(f"malformed alias {alias!r}: more than one '@'")
    alias = alias.replace("@", ".")
    if "." not in alias:
        raise NotAnAlias(f"{alias!r} looks like a raw address, not an alias")

    fqdn = _to_ascii(alias)
    labels = fqdn.split(".")
    if any(not label for label in labels):
        raise OpenAliasError(f"malformed alias {alias!r}: contains an empty label")
    if len(fqdn) > 253 or any(len(label) > 63 for label in labels):
        raise OpenAliasError(f"alias {alias!r} exceeds DNS length limits")
    return fqdn


# --- DNS lookup --------------------------------------------------------------

def _authenticated_txt(name: str) -> list[list[bytes]]:
    """Return the TXT records at `name`, locally DNSSEC-validated (see dnssec.py).

    Returns an empty list when the name has no such records. Raises
    `InsecureLookup` if the answer cannot be validated (fail closed), or
    `LookupFailed` if the lookup itself fails.
    """
    try:
        return dnssec.secure_txt(name)
    except dnssec.Insecure as exc:
        raise InsecureLookup(str(exc)) from exc
    except dnssec.Unavailable as exc:
        raise LookupFailed(str(exc)) from exc


# --- record parsing ----------------------------------------------------------

def parse_record(strings: list[bytes]) -> dict | None:
    """Parse one TXT record (its character-strings) into a {key: value} dict.

    Follows the OA2 Key-Value Encoding rules: character-strings are concatenated
    with no separator; pairs are split on ';'; each pair splits on its first
    '='; keys are lowercased. Returns None for a record that is not valid UTF-8,
    contains a malformed key, or repeats a key — such records must be rejected
    rather than guessed at.
    """
    try:
        text = b"".join(strings).decode("utf-8")
    except UnicodeDecodeError:
        return None

    fields: dict[str, str] = {}
    for pair in text.split(";"):
        pair = pair.strip()  # tolerate the optional space after ';' and a trailing ';'
        if not pair:
            continue
        if "=" not in pair:
            return None  # a non-empty pair without '=' is malformed
        key, value = pair.split("=", 1)  # only the first '=' is significant
        key = key.strip().lower()
        if not key or any(char not in _KEY_CHARS for char in key):
            return None  # keys are ASCII letters, digits, and underscores
        if key in fields:
            return None  # a repeated key means the record is ambiguous
        fields[key] = value
    return fields


def records(alias: str, prefix: str) -> list[dict]:
    """Resolve every OA2 record under `prefix` for `alias` as raw {key: value} dicts."""
    name = f"{prefix}.{normalize(alias)}"
    parsed = (parse_record(strings) for strings in _authenticated_txt(name))
    return [fields for fields in parsed if fields and fields.get("oa_version") == "2"]


# --- payment records ---------------------------------------------------------

@dataclass(frozen=True)
class PaymentRecord:
    """A single `_openalias-payment` record."""

    network: str
    address: str
    asset: str | None = None
    address_type: str | None = None
    priority: int | None = None
    amount: Decimal | None = None
    memo: str | None = None
    fields: dict = field(default_factory=dict, repr=False)  # every raw pair, incl. unknown keys

    @property
    def effective_asset(self) -> str:
        """The asset being paid; an omitted asset means the network's native asset."""
        return self.asset or self.network


def _payment_from_fields(fields: dict) -> PaymentRecord | None:
    """Build a PaymentRecord, or None if a required field is missing."""
    network, address = fields.get("network"), fields.get("address")
    if not network or not address:
        return None  # network and address are required

    priority = None
    if "priority" in fields:
        try:
            priority = int(fields["priority"])
        except ValueError:
            priority = None  # a malformed priority sorts last

    amount = None
    if "amount" in fields:
        try:
            amount = Decimal(fields["amount"])
        except InvalidOperation:
            amount = None  # amount is only a hint; ignore it if malformed

    return PaymentRecord(
        network=network,
        address=address,
        asset=fields.get("asset"),
        address_type=fields.get("address_type"),
        priority=priority,
        amount=amount,
        memo=fields.get("memo"),
        fields=fields,
    )


def payments(alias: str) -> list[PaymentRecord]:
    """Resolve payment records for `alias`, most-preferred first.

    Records are ordered by `priority` (lower is higher priority); a record with
    no priority sorts last.
    """
    parsed = (_payment_from_fields(fields) for fields in records(alias, PAYMENT_PREFIX))
    found = [record for record in parsed if record is not None]
    found.sort(key=lambda r: r.priority if r.priority is not None else float("inf"))
    return found


def metadata(alias: str) -> dict | None:
    """Resolve the first `_openalias-metadata` record for `alias`, or None."""
    found = records(alias, METADATA_PREFIX)
    return found[0] if found else None


# --- native asset ------------------------------------------------------------

_native_assets = None


def native_asset(network: str) -> str | None:
    """Return the `asset` id of `network`'s native asset, per the OA2 network list.

    Returns None if the network is unknown or lists no native asset. The mapping
    is explicit (not inferred from the network code), so networks whose native
    asset differs from their code — e.g. `base` -> `eth` — resolve correctly.
    """
    global _native_assets
    if _native_assets is None:
        _native_assets = {}
        with open(NETWORK_LIST_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                net = (row.get("OpenAlias network") or "").strip()
                if net:
                    _native_assets[net] = (row.get("Network Native asset") or "").strip() or None
    return _native_assets.get(network)


def is_native(record: PaymentRecord) -> bool:
    """True if `record` pays its network's native asset.

    Native is signalled either by omitting `asset` or by stating the asset the
    network list records as native — so both `network=xmr` and the explicit
    `network=xmr; asset=xmr` count as native, as does `network=base; asset=eth`.
    """
    return record.asset is None or record.asset == native_asset(record.network)
