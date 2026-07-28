"""
dnssec.py — locally validate DNSSEC-signed DNS answers.

Records (and their RRSIGs, DNSKEYs, and DS records) are fetched through the
system resolver, but that resolver is NOT trusted: every signature is verified
inside this process, up a chain of trust anchored at the IANA root key. A
resolver — or a network attacker between us and it — that tampers with the data
is caught, because it cannot forge the signatures.

Scope: this validates the chain of trust for a *positive* answer. It does not
prove authenticated denial of existence (NSEC/NSEC3), so a name with no records
is reported as empty without a secure proof of that absence.

Requires: dnspython with cryptography  ->  pip install "dnspython[dnssec]"
"""

from __future__ import annotations

import dns.dnssec
import dns.exception
import dns.flags
import dns.name
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.resolver

TIMEOUT = 10.0  # seconds per DNS lookup

# IANA root trust anchor: the root key-signing key (KSK-2017, key tag 20326),
# published at https://data.iana.org/root-anchors/. Anchoring validation here is
# what lets us distrust the resolver we query.
_ROOT_ANCHOR = dns.rdata.from_text(
    dns.rdataclass.IN,
    dns.rdatatype.DS,
    "20326 8 2 E06D44B80B8F1D39A95C0B0D7C65D08458E880409BBC683457104237C7F8EC8D",
)

_DIGEST_NAME = {1: "SHA1", 2: "SHA256", 4: "SHA384"}


class DNSSECError(Exception):
    """Base class for lookup and validation errors."""


class Insecure(DNSSECError):
    """The answer is unsigned, fails validation, or has no chain to the root."""


class Unavailable(DNSSECError):
    """The DNS lookup itself failed (network error, SERVFAIL, timeout, ...)."""


_resolver = None


def _fetch(name, rdtype):
    """Return (rrset, rrsig) for name/rdtype, fetched through the system resolver.

    The resolver is used only as transport for signed data, so it need not
    validate or be trusted. Either element is None if the record is absent.
    """
    global _resolver
    if _resolver is None:
        _resolver = dns.resolver.Resolver()
        _resolver.use_edns(0, dns.flags.DO, 1232)  # ask for the DNSSEC records
        _resolver.lifetime = TIMEOUT
    try:
        answer = _resolver.resolve(name, rdtype, raise_on_no_answer=False)
    except dns.resolver.NXDOMAIN:
        return None, None
    except dns.exception.DNSException as exc:
        raise Unavailable(f"{name} {dns.rdatatype.to_text(rdtype)}: {exc}") from exc
    section = answer.response.answer
    rrset = answer.response.get_rrset(section, name, dns.rdataclass.IN, rdtype)
    rrsig = answer.response.get_rrset(
        section, name, dns.rdataclass.IN, dns.rdatatype.RRSIG, covers=rdtype
    )
    return rrset, rrsig


def _verify(rrset, rrsig, keys):
    """Verify `rrset` against `rrsig` using `keys` (a {zone: DNSKEY rrset} map)."""
    if rrset is None or rrsig is None:
        raise Insecure("a record or its signature is missing")
    try:
        dns.dnssec.validate(rrset, rrsig, keys)
    except dns.dnssec.ValidationFailure as exc:
        raise Insecure(f"signature did not validate: {exc}") from exc


def _key_matches(zone, dnskey_rrset, ds_records):
    """True if some key in `dnskey_rrset` hashes to one of `ds_records`."""
    for ds in ds_records:
        digest = _DIGEST_NAME.get(ds.digest_type)
        if digest is None:
            continue  # unknown digest algorithm
        for key in dnskey_rrset:
            try:
                if dns.dnssec.make_ds(zone, key, digest) == ds:
                    return True
            except dns.dnssec.ValidationFailure:
                continue
    return False


def _trusted_keys(zone):
    """Validate the chain of trust from the root down to `zone`.

    Returns `zone`'s validated DNSKEY rrset. Each zone's parent is discovered
    from the signer of that zone's DS signature, so zone cuts are located
    correctly even under multi-label suffixes such as `co.uk`.
    """
    # Walk up from `zone` to the root, collecting each zone's (signed) DS record.
    delegations = []  # (zone, ds_rrset, ds_rrsig), ordered child -> parent
    current = zone
    while current != dns.name.root:
        ds, ds_sig = _fetch(current, dns.rdatatype.DS)
        if ds is None or ds_sig is None:
            raise Insecure(f"{current}: no signed DS record (broken chain of trust)")
        delegations.append((current, ds, ds_sig))
        current = ds_sig[0].signer  # the parent zone that signed this DS

    # Establish trust at the root from the built-in anchor.
    root_keys, root_sig = _fetch(dns.name.root, dns.rdatatype.DNSKEY)
    if not _key_matches(dns.name.root, root_keys, [_ROOT_ANCHOR]):
        raise Insecure("root DNSKEY does not match the trust anchor")
    _verify(root_keys, root_sig, {dns.name.root: root_keys})

    # Walk back down: each DS is signed by its parent's keys and, in turn,
    # authenticates the child zone's keys.
    parent_zone, parent_keys = dns.name.root, root_keys
    for zone_name, ds, ds_sig in reversed(delegations):
        _verify(ds, ds_sig, {parent_zone: parent_keys})       # DS signed by the parent
        zone_keys, zone_sig = _fetch(zone_name, dns.rdatatype.DNSKEY)
        if zone_keys is None:
            raise Insecure(f"{zone_name}: no DNSKEY record")
        if not _key_matches(zone_name, zone_keys, ds):         # a key matches the DS
            raise Insecure(f"{zone_name}: no DNSKEY matches its DS")
        _verify(zone_keys, zone_sig, {zone_name: zone_keys})   # DNSKEY set self-signed
        parent_zone, parent_keys = zone_name, zone_keys

    return parent_keys


def secure_txt(name: str) -> list[list[bytes]]:
    """Fetch and locally validate the TXT records at `name`.

    Returns each record's character-strings (bytes), or [] if the name has no
    TXT records. Raises `Insecure` if the answer cannot be validated to the
    root, or `Unavailable` if the lookup fails.
    """
    qname = dns.name.from_text(name)
    txt, txt_sig = _fetch(qname, dns.rdatatype.TXT)
    if txt is None:
        return []  # no records (note: this absence is not securely proven)
    if txt_sig is None:
        raise Insecure(f"{name}: the TXT records are not signed")

    signer = txt_sig[0].signer  # the zone whose key signed the records
    _verify(txt, txt_sig, {signer: _trusted_keys(signer)})
    return [list(rdata.strings) for rdata in txt]
