# OpenAlias v2 Specification

## Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only when, they appear in all capitals, as shown here.

## OA2 Format

OpenAlias v2 introduces new OpenAlias record types.

### Key-Value Encoding

Both `_openalias-metadata` and `_openalias-payment` records encode their contents as a series of `key=value` pairs. The following rules define how these records are written and parsed:

* Pairs are separated by a semicolon (`;`). A single optional space MAY follow the semicolon for readability, and a trailing semicolon MAY be present. For example: `key1=value1; key2=value2;`.
* Within each pair, the key and value are separated by the first equals sign (`=`). A value can therefore contain further `=` characters (for example, in a URL query string); only the first `=` is significant.
* A value MUST NOT contain a semicolon (`;`), which is reserved as the pair separator. If a value needs to convey a semicolon (for example, inside a URL), it MUST be percent-encoded as `%3B`. Free-text values such as `name` and `description` MUST NOT contain semicolons.
* Keys are case-insensitive and consist of ASCII letters, digits, and underscores. Values are interpreted as UTF-8.
* Parsers MUST ignore unrecognized keys, so that new keys can be added in the future without breaking existing clients.
* A record that repeats a key that has a defined meaning (for example, two `address` values) MUST be rejected rather than guessed.
* DNS software can split a single TXT record into multiple character-strings of up to 255 bytes each. Clients MUST concatenate these character-strings in order, with no separator, before parsing (see [RFC 7208, Section 3.3](https://www.rfc-editor.org/rfc/rfc7208#section-3.3)). Record publishers do not need to split values manually; DNS providers handle this automatically.

### `_openalias-metadata`

`_openalias-metadata` contains various items that are useful across different record types. For example, you can specify a name, image link, social profile links, social profile usernames, or other information.

Example name and image for `donate@openalias.org`:

* TXT name: `_openalias-metadata.donate`
* TXT content: `oa_version=2; name=OpenAlias Project; image=https://openalias.org/image.png;`

#### `_openalias-metadata` Key-Value Pairs

OA2 does not maintain an official list of all `_openalias-metadata` key-value pairs. All key-value pairs are optional. Developers are free to create their own unique key-value pairs. The following are somewhat standardized for common use:

* `oa_version`: The OpenAlias version; always `2` for OpenAlias v2
* `name`: Intended as a display name for the recipient, e.g. "Satoshi Nakamoto".
* `description`: Intended as a description for the transaction, e.g. "Donation to project development".
* `image`: Intended as a display image when interacting with the recipient. More details below.
* `twitter`: Intended for a Twitter username, e.g. "AP" (excludes the `@`).
* `nostr`: Intended for a Nostr username.
* `signal`: Intended for a Signal messenger username.
* `telegram`: Intended for a Telegram username.

#### `image`

This is an optional link to an image file on the ***same*** domain and subdomain as the TXT record. For example:

> image=https://getmonero.org/press-kit/symbols/monero-symbol-on-white-480.png

Wallet developers MUST prohibit image (and other metadata) lookups to links on another domain or subdomain. The image MUST be served over HTTPS on the same domain and subdomain as the TXT record. To keep this restriction from being bypassed, clients MUST NOT follow redirects to a different domain or subdomain, and SHOULD enforce reasonable limits on the response size and content type.

### `_openalias-payment`

`_openalias-payment` is a series of TXT records for communicating payment information.

The TXT record name begins with `_openalias-payment`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-payment.`. For `example.openalias.org`, the subdomain would be `_openalias-payment.example`.

The TXT content strictly uses key-value pairs. The key-value pairs are as follows:

| Key | Example Value | Required? | Description |
| --- | --- | --- | --- |
| `oa_version` | `2` | Yes | Always `2` for OpenAlias v2 |
| `priority` | `10` | No | Integer; lower number is higher priority |
| `network` | `btc` | Yes | The asset network |
| `asset` | `btc` | No | The asset name/ticker or asset address; defaults to the network's native asset |
| `address` |  | Yes | The full address |
| `address_type` | `bip352` | No | The address type |
| `amount` | `0.01` | No | A requested amount in the asset's standard units (see below) |
| `memo` |  | No | A memo, destination tag, or similar identifier (see below) |

One example:

> oa_version=2; priority=10; network=btc; address=sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v; address_type=bip352;

#### `network` and `asset`

`network` is required; it refers to the blockchain network. `asset` is recommended; it refers to the ticker or contract address on the network. If `asset` is omitted, it defaults to the network's native asset (for example, `network=btc` alone denotes BTC on Bitcoin).

This is a major improvement from OA1. Instead of simply specifying `usdt` as the prefix, recordholders can specify the exact network that they wish to receive USDT on, e.g. `network=eth; asset=usdt;`. Priorities can be further specified.

Either a nickname can be used for the `asset` or the full token address/ID. For example, the Uniswap token on Ethereum can be represented as either `asset=uni` or `asset=0x1f9840a85d5af5bf1d1762f925bdaddc4201f984`.

#### `address_type`

The `address_type` is an optional (but recommended) identifier for the address type. Example address types might be `p2tr`, `p2wpkh`, `p2sh`, `p2pkh`, `bip352` (silent payments address), `bip47` (PayNym). Recognized values are listed in the `address_type` list (see below).

#### `amount`

`amount` is an optional, requested amount expressed in the asset's standard (display) units as a decimal value. For example, 0.01 BTC is written as `amount=0.01`, never in a smaller unit such as satoshis.

Interpreting `amount` requires knowing how many decimal places the asset's standard unit has. The OA2 asset list suggests a `Decimals` value for this purpose (see below), but it is only a suggestion — many networks define this themselves (for example, ERC-20 tokens publish their own `decimals` on-chain), so a client MAY use whatever source it considers authoritative. Where no suggestion is available, the client SHOULD apply its own sensible interpretation for the asset.

`amount` is a request, not a constraint: a wallet SHOULD treat it as a suggested value to prefill, and the sender remains free to choose the amount they send.

#### `memo`

`memo` is an optional, network-specific identifier for networks that require or support one, such as an XRP destination tag, a Stellar memo, or a (legacy) Monero payment ID. Its format and meaning are defined by the destination network.

## OA2 Lists

For OA1, there was an expressed interest in maintaining an official list of prefixes, but this never materialized.

For OA2, OpenAlias should publish standardized lists for `asset` (for major assets only), `network`, and `address_type`.

OA2 should maintain a list that maps `network` and `asset` values to [CAIP-2](https://chainagnostic.org/CAIPs/caip-2) and [CAIP-19](https://chainagnostic.org/CAIPs/caip-19), respectively. The `network` list also records each network's native asset — the `asset` value that denotes it — so a native-asset payment is recognized even when the `asset` is stated explicitly (for example, `network=xmr; asset=xmr`) rather than omitted. This mapping is explicit rather than inferred from the network code, because a network's native asset need not share its code (for example, the native asset on `base` is `eth`). The `asset` list also includes a `Decimals` column suggesting the number of decimal places in the asset's standard unit, which clients may use when interpreting the payment `amount`. The `address_type` list enumerates recognized address types, each anchored to the `network` it applies to. OA2 does not plan to maintain a list of key-value pairs for metadata records.

These lists are available in the `/oa2-lists` folder as `network.csv` (the `network` list), `asset.csv` (the `asset` list), and `address_type.csv` (the `address_type` list).

### Proposing Changes (Additions/Deletions/Modifications) to the Lists

Please open a pull request to suggest changes to an existing list. In your pull request, make sure to follow the proper formatting of the destination list.

## Resolving OpenAlias Records

To resolve an OpenAlias, an implementation performs the following steps:

1. Normalize the input. If the value contains an `@`, replace it with a `.` (period) to convert an email-style alias (`donate@openalias.org`) into a fully qualified domain name (`donate.openalias.org`). If the value contains no `.`, treat it as a raw address rather than an alias. Internationalized domain names MUST be converted to their [A-label (Punycode)](https://www.rfc-editor.org/rfc/rfc5890) form.
2. Construct the record names. For an alias `<label>.<domain>`, payment records are found at `_openalias-payment.<label>.<domain>` and metadata at `_openalias-metadata.<label>.<domain>`. For an alias that is a bare domain (for example, `openalias.org`), use `_openalias-payment.openalias.org` and `_openalias-metadata.openalias.org`.
3. Query TXT records. Fetch the TXT records at the `_openalias-payment` name, retrying on transient failure. A single name can return several payment records — one per address. Metadata MAY be fetched from the `_openalias-metadata` name when the application displays it.
4. Validate DNSSEC. The lookup MUST fail unless there is a valid DNSSEC trust chain, as described under Security Considerations and Requirements.
5. Parse each record. Concatenate the TXT character-strings and parse the key-value pairs as described under Key-Value Encoding. Reject any record whose `oa_version` is not `2` or that omits a required field.
6. Select a record. Filter to the records the sender is able to pay (by `network` and `asset`), then apply priority as described under Choosing Priorities.
7. Confirm with the user. Present the resolved address, and any metadata, for the user to verify before sending.

## Security Considerations and Requirements

There MUST be a valid DNSSEC trust chain (RRSIG, DNSKEY, NSEC3), or else the OpenAlias lookup MUST fail. DNSSEC is much more widely supported than it was when the OA1 standard was created.

Clients MUST ensure this validation is trustworthy. They SHOULD either perform DNSSEC validation locally, or delegate it to a validating resolver reached over an authenticated, encrypted channel (such as DNS over HTTPS or DNS over TLS). A client MUST NOT rely solely on the authenticated-data (AD) bit returned by an untrusted resolver over an unauthenticated channel, since a network attacker can forge that bit.

## Privacy Considerations and Requirements

When fetching metadata from links, such as an image, this will leak the user's IP address to that server.

The DNS lookups themselves also carry privacy risk: a resolver or on-path observer can see which alias a user is resolving, which can reveal who they intend to pay. Implementations SHOULD protect these queries, for example by using DNS over HTTPS, DNS over TLS, or DNSCrypt with a resolver that does not log queries.

Implementations MUST restrict metadata link lookups to the specific domain and subdomain.

Implementations SHOULD consider opt-in user consent before fetching content from links. This can be done through an application setting or requested in each situation.

Implementations SHOULD consider proxying link information requests if they already proxy other information for users.

## Choosing Priorities

OpenAlias v2 does not mandate a specific process for choosing the priority of records for sending transactions. Ultimately, a recipient should be willing to accept assets through all of their posted addresses, and a sender can only send transactions that they consent to create.

`priority` is a single ordering across all of a recipient's payment records, applied after the sender has filtered to the records it is able to pay. A lower number is higher priority. A record without a `priority` is treated as the lowest priority. When two eligible records share the same priority, the choice between them is left to the implementation, which MAY present them to the user.

OpenAlias v2 recommends that implementers pick one of these options:

1. Prefer the recipient priority. Select the highest priority option that is supported by the sender.
2. Compare the highest-priority record according to the recipient that the sender supports sending to with the highest-priority record from the sender's perspective. Allow the sender to select their choice of these.

## Test Vectors

The following non-normative examples illustrate how records are named, published, and parsed. Addresses are illustrative.

### Resolving an email-style alias

Input: `donate@openalias.org`, which normalizes to the FQDN `donate.openalias.org`. The client queries TXT records at `_openalias-payment.donate.openalias.org` and `_openalias-metadata.donate.openalias.org`.

Metadata record at `_openalias-metadata.donate.openalias.org`:

> oa_version=2; name=OpenAlias Project; image=https://openalias.org/image.png;

Payment records at `_openalias-payment.donate.openalias.org`, returned as two TXT records in one RRset:

> oa_version=2; priority=10; network=btc; address=sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v; address_type=bip352;

> oa_version=2; priority=20; network=xmr; address=46BeWrHpwXmHDpDEUmZBWZfoQpdc6HaERCNmx1pEYL2rAcuwufPN9rXHHtyUA4QVy66qeFQkn6sfK8aHYjA3jk3o1Bv16em;

The result is two payment options with the display name "OpenAlias Project". Ordered by priority, the Bitcoin record (`priority=10`) is preferred over the Monero record (`priority=20`). The Bitcoin record omits `asset`, so it denotes the network's native asset (BTC).

### Ignoring unrecognized keys

A record can contain keys a client does not recognize; the client ignores them and parses the rest:

> oa_version=2; network=btc; address=sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v; future_field=somevalue;

This parses to a Bitcoin payment; `future_field` is ignored.

### Concatenating a multi-string TXT record

DNS can deliver one record as multiple character-strings (shown here as two adjacent quoted strings). The client concatenates them, in order, with no separator, before parsing:

> "oa_version=2; network=xmr; address=46BeWrHpwXmHDpDEUmZBWZfoQpdc6HaERCNmx1pEYL2rAcuwufPN9rXHHtyUA4QV" "y66qeFQkn6sfK8aHYjA3jk3o1Bv16em;"

This is equivalent to the single value:

> oa_version=2; network=xmr; address=46BeWrHpwXmHDpDEUmZBWZfoQpdc6HaERCNmx1pEYL2rAcuwufPN9rXHHtyUA4QVy66qeFQkn6sfK8aHYjA3jk3o1Bv16em;

### Resolving an internationalized domain name

Input: `bob@münchen.example`. The Unicode label is converted to its A-label before querying, so the client queries TXT at `_openalias-payment.bob.xn--mnchen-3ya.example`.

### Native asset when it differs from the network code

On Base, the native asset is `eth`, not `base` (the `network` list records this). A native-asset payment on Base is therefore expressed in either of these equivalent ways:

> oa_version=2; network=base; address=0x71C7656EC7ab88b098defB751B7401B5f6d8976F;

> oa_version=2; network=base; asset=eth; address=0x71C7656EC7ab88b098defB751B7401B5f6d8976F;

Both resolve to the same native asset (`eth`) on Base: the first omits `asset` (native by default), and in the second `asset=eth` matches the network's recorded native asset. A client MUST treat the two as equivalent, and MUST NOT treat `asset=eth` here as a token distinct from the native asset.

## Example Implementations

Two runnable examples in [`/oa2-examples`](/oa2-examples) resolve OpenAlias v2 records with the same structure and trust model: the answer is DNSSEC-validated to the DNS root, and lookups fail closed on anything that cannot be validated.

### Python

Uses [dnspython](https://www.dnspython.org/) (`pip install "dnspython[dnssec]"`) and validates DNSSEC locally, in-process, against the root trust anchor.

* [`openalias.py`](/oa2-examples/python/openalias.py) — the resolution library: alias normalization, record parsing, and typed payment records.
* [`dnssec.py`](/oa2-examples/python/dnssec.py) — local DNSSEC validation: fetches records through the system resolver but verifies every signature in-process against the root trust anchor.
* [`wallet.py`](/oa2-examples/python/wallet.py) — resolve an alias, select a supported payment record by priority, and confirm the address before sending.
* [`fetch_all_records.py`](/oa2-examples/python/fetch_all_records.py) — print every OA2 payment and metadata record for an alias.

### Dart

Mirrors the Python example. Pure Dart has no practical local DNSSEC validator, so the validating lookup runs in a small Rust helper (using [hickory](https://github.com/hickory-dns/hickory-dns)) called over FFI — the same approach [Skylight Wallet](https://github.com/MAGICGrants/skylight-wallet) takes. See the [README](/oa2-examples/dart/README.md) for build steps.

* [`openalias.dart`](/oa2-examples/dart/openalias.dart) — the resolution library: FFI to the native resolver, record parsing, typed records, and selection.
* [`native/`](/oa2-examples/dart/native) — the Rust helper doing DNSSEC-validated TXT resolution.
* [`wallet.dart`](/oa2-examples/dart/wallet.dart) — resolve an alias, select a supported payment record by priority, and confirm the address before sending.
* [`fetch_all_records.dart`](/oa2-examples/dart/fetch_all_records.dart) — print every OA2 payment and metadata record for an alias.

## FAQ

### Why not use CAIP-2 and CAIP-19 directly for `network` and `asset`?

CAIP references other [namespace](https://namespaces.chainagnostic.org/) standards. For example, the CAIP-2 blockchain identifiers for the following common assets are:

| Blockchain Friendly Name | CAIP-2 | OpenAlias `network` |
| --- | --- | --- |
| Bitcoin Mainnet | `bip122:000000000019d6689c085ae165831e93` | `btc` |
| Monero Mainnet | `monero:418015bb9ae982a1975da7d79277c270` | `xmr` |
| Litecoin Mainnet | `bip122:12a765e31ffd4059bada1e25190f6e98` | `ltc` |

Likewise, CAIP-19 references other [namespaces](https://namespaces.chainagnostic.org/), with `slip144` being the primary namespace outside ecosystem-specific ones. The following example CAIP-19 asset identifiers are:

| Blockchain Friendly Name | CAIP-19 | OpenAlias `network` and `asset` |
| --- | --- | --- |
| Uniswap on Ethereum | `eip155:1/erc20:0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` | `eth; uni` or `eth; 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` |
| XMR on Monero | `monero:418015bb9ae982a1975da7d79277c270/slip44:128` | `xmr; xmr` |
| BTC on Bitcoin | `bip122:000000000019d6689c085ae165831e93/slip44:0` | `btc; btc` |
| LTC on Litecoin | `bip122:12a765e31ffd4059bada1e25190f6e98/slip44:2` | `ltc; ltc` |

Including CAIP-2 and CAIP-19 in their entirety is overkill for OpenAlias purposes. Supporting native use of CAIP-2 and CAIP-19 in OpenAlias records would add these [namespaces](https://namespaces.chainagnostic.org/) as a dependency. The benefits of allowing CAIP natively in OpenAlias seem to create more work and complexity overall; however, this could be reconsidered if CAIP is widely adopted in nearly all wallets.

Nevertheless, CAIP-2 and CAIP-19 are useful for mapping OpenAlias `network` and `asset` values for completeness.

### Why not support stagenet/testnet? Why only mainnet?

OpenAlias test sending flows can be accomplished without sending transactions, since it is an address and metadata lookup standard. Thus, there is little additional value to be achieved by the increased complexity of supporting networks that are only used for testing purposes.

### Does OpenAlias aim to allow other record standards (ENS, Unstoppable Domains) to directly work with OpenAlias?

No. OpenAlias will not aim to directly support other standards. However, OpenAlias aims to avoid conflicting with other standards.

One long-term goal could be to build a universal library that allows interpreting a variety of standards including OpenAlias and other popular standards.

### Why were _openalias-routing records dropped from the OA2 specification?

Despite the added complexity, it did not provide the features that were desired. Allowing a priority per `_openalias-payment` records is simpler *and* more thorough.

## Compatibility with OA1

OA1 and OA2 records can coexist for the same recipient because they live at different names: OA1 records are published on the alias FQDN directly, while OA2 records are published under the `_openalias-payment` and `_openalias-metadata` prefixes. A client that supports both MUST prefer OA2: when any OA2 records are present it MUST use them, falling back to OA1 only when no OA2 records exist.

OpenAlias records are versioned both by record name and by the `oa_version` field. The `_openalias-payment` and `_openalias-metadata` names identify a record as OA2, and `oa_version=2` states the version explicitly within each record. A future revision would introduce a new `oa_version` value (and, if needed, new record names), so that newer records can be added without breaking existing OA1 or OA2 clients.

## Limitations of OA1

* Since it was created in 2014/2015 before Ethereum and before it was common to have tokens on multiple blockchains, OA1 does not sensibly allow for passing the network for a given asset. ETH on Ethereum mainnet might be `eth`, but ETH on Polygon might have to be `eth_poly` or similar. This is inelegant.
* Arguably, the length of several key-value pairs are longer than they need to be.
* There is no priority. Suppose someone wants to be paid in USDT, and they prefer to receive it on Ethereum, then failing that, on Polygon.
* OA1 does not attempt to indicate the address type, which might be very useful for certain Bitcoin applications.
* OpenAlias records are not organized into a dedicated OpenAlias section, which may result in clutter.

## Advantages of OA1

* DNS TXT records with DNSSEC remains one of the simplest and most robust ways to handle these alias lookups.
* OA1 includes a version number, which means we can upgrade to a new OA2 without breaking existing OA1 records.
* OA1 works for arbitrary assets, not just BTC or ETH.
* OA1 is supported by major wallets Electrum, Cake Wallet, the official Monero wallets, Feather Wallet and more.
* OA1 makes it simple for a user to "sanity check" the DNS record resolves to their intended address destination, since the visible address in the record is the same address that a user copies from their wallet software.

## Avoiding Conflicting Standards

OA1 and OA2 do not need to be compatible with every other alias standard, but we should avoid conflicting with them where possible. Some notable ones are:

* Ethereum Name Service (ENS)
* Namecoin
* Unstoppable Domains
* https://github.com/bitcoin/bips/pull/1551
* [Chain Agnostic Improvement Proposals](https://chainagnostic.org)
