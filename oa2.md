# OpenAlias v2 Specification

## OA2 Format

OpenAlias v2 introduces new OpenAlias record types.

### `_openalias-metadata`

`_openalias-metadata` contains various items that are useful across different record types. For example, you can specify a name, image link, social profile links, social profile usernames, or other information.

Example name and image for `donate@openalias.org`:

* TXT name: `_openalias-metadata.donate`
* TXT content: `oa2 name=OpenAlias Project; image=https://openalias.org/image.png`

#### `_openalias-metadata` Key-Value Pairs

OA2 does not maintain an official list of all `_openalias-metadata` key-value pairs. All key-value pairs are optional. Developers are free to create their own unique key-value pairs. The following are somewhat standardized for common use:

* `oa_version`: The OpenAlias version, so `2`
* `name`: Intended as a display name for the recipient, e.g. "Satoshi Nakamoto".
* `description`: Intended as a description for the transaction, e.g. "Donation to project development".
* `checksum`: Intended as a checksum. More details below.
* `image`: Intended as a display image when interacting with the recipient. More details below.
* `twitter`: Intended for a Twitter username, e.g. "AP" (excludes the `@`).
* `nostr`: Intended for a Nostr username.
* `signal`: Intended for a Signal messenger username.
* `telegram`: Intended for a Telegram username.

#### `image`

This is an optional link to an image file on the ***same*** domain and subdomain as the TXT record. For example:

> image=https://getmonero.org/press-kit/symbols/monero-symbol-on-white-480.png

Wallet developers MUST prohibit image (and other metadata) lookups to links on another domain or subdomain.

### `_openalias-payment`

`_openalias-payment` are a series of TXT records for communicating payment information.

The TXT record name begins with `_openalias-payment`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-payment.`. For `example.openalias.org`, the subdomain would be `_openalias-payment.example`.

The TXT content strictly uses key-value pairs. The key-value pairs are as follows:

| Key | Example Value | Required? | Description |
| --- | --- | --- | --- |
| `oa_version` | `2` | Yes | Always `2` for OpenAlias v2 |
| `priority` | `10` | No | Integer; lower number is higher priority |
| `network` | `btc` | Yes | The asset network |
| `asset` | `btc` | No | The asset name/ticker or asset address |
| `address` |  | Yes | The full address |
| `address_type` | bip352 | No | The address type |
| `amount` | `10` | No | The amount in asset (or network) value |
| `payment_id` |  | No | A payment ID,  tag, or similar identifier |

One example:

> oa_version=2; priority=10; network=btc; address=sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v; address_type=bip352;

#### `network` and `asset`

`network` is required; it refers to the blockchain network. `asset` is recommended; it refers to the ticker or contract address on the network blockchain.

This is a major improvement from OA1. Instead of simply specifying `usdt` as the prefix, recordholders can specify the exact network that they wish to receive USDT on, eg: `network=eth; asset=usdt;`. Priorities can be further specified.

Either a nickname can be used for the `asset` or the full token address/ID. For example, the Uniswap token on Ethereum can be represented as either `asset=uni` or `asset=0x1f9840a85d5af5bf1d1762f925bdaddc4201f984`.

#### `address_type`

The `address_type` is an optional (but recommended) identifier for the address type. Example address types might be `p2tr`, `p2wpkh`, `p2sh`, `p2pkh`, `bip352` (silent payments address), `bip47` (PayNym).

## OA2 Lists

For OA1, there was an expressed interest in maintaining an official list of prefixes, but this never materialized.

For OA2, OpenAlias should publish standardized lists for `asset` (for major assets only), `network`, and `address_type`.

OA2 should maintain a list that maps `network` and `asset` values to [CAIP-2](https://chainagnostic.org/CAIPs/caip-2) and [CAIP-19](https://chainagnostic.org/CAIPs/caip-19), respectively. OA2 does not plan to maintain a list of key-value pairs for metadata records.

These lists are available in the `/oa2-lists` folder.

### Proposing Changes (Additions/Deletions/Modifications) to the Lists

Please open a pull request to suggest changes to an existing list. In your pull request, make sure to follow the proper formatting of the destination list.

## Security Considerations and Requirements

There must be a valid DNSSEC trust chain (RRSIG, DNSKEY, NSEC3), or else the OpenAlias lookup must fail. DNSSEC is much more widely supported than it was when the OA1 standard was created.

## Privacy Considerations and Requirements

When fetching metadata from links, such as an image, this will leak the user's IP address to that server.

Implementations must restrict metadata link lookups to the specific domain and subdomain.

Implementations should consider opt-in user consent before fetching content from links. This can be done through an application setting or requested in each situation.

Implementations should consider proxying link information requests if they already proxy other information for users.

## Choosing Priorities

OpenAlias v2 does not mandate a specific process for choosing the priority of records for sending transactions. Ultimately, a recipient should be willing to accept assets through all of their posted addresses, and a sender can only send transfactions that they consent to create.

OpenAlias v2 recommends that implementers pick one of these options:

1. Prefer the recipient priority. Select the highest priority option that is supported by the sender.
2. Compare the highest-priority record according to the recipient that the sender supports sending to with the highest-priority record from the sender's perspective. Allow the sender to select their choice of these.

## Python Examples

*Forthcoming*

* [Wallet example](/oa2-examples/python-wallet.py)
* [Fetch all records example](/oa2-examples/python-fetch-all-records.py)

## FAQ

### Why not use CAIP-2 and CAIP-19 directly for `network` and `asset`?

CAIPs references other [namespace](https://namespaces.chainagnostic.org/) standards. For example, the CAIP-2 blockchain identifiers for the following common assets are:

| Blockchain Friendly Name | CAIP-2 | OpenAlias `network` |
| --- | --- | --- |
| Bitcoin Mainnet | `bip122:000000000019d6689c085ae165831e93` | `btc` |
| Monero Mainnet | `monero:418015bb9ae982a1975da7d79277c270` | `xmr` |
| Litecoin Mainnet | `bip122:12a765e31ffd4059bada1e25190f6e98` | `ltc` |

Likewise, CAIP-19 references other [namespaces](https://namespaces.chainagnostic.org/), with `slip144` being the primary namespace outside ecosystem-specific ones. The following example CAIP-19 asset identifiers are:

| Blockchain Friendly Name | CAIP-19 | OpenAlias `network` and `asset` |
| --- | --- | --- |
| Uniswap on Ethereum | `eip155:1/erc20:0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` | `eth; uni` or `eth; 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` |
| XMR on Monero | `monero:418015bb9ae982a1975da7d79277c270/slip44:128` | `xmr/xmr` |
| BTC on Bitcoin | `bip122:000000000019d6689c085ae165831e93/slip44:0` | `btc/btc` |
| LTC on Litecoin | `bip122:12a765e31ffd4059bada1e25190f6e98/slip44:2` | `ltc/ltc` |

Including CAIP-2 and CAIP-19 in their entirety is overkill for OpenAlias purposes. Supporting native use of CAIP-2 and CAIP-19 in OpenAlias records would add these [namespaces](https://namespaces.chainagnostic.org/) as a dependency. The benefits of allowing CAIP natively in OpenAlias seems to create more work and complexity overall; however, this could be reconsidered if CAIP is widely adopted in nearly all wallets.

Nevertheless, CAIP-2 and CAIP-19 are useful for mapping OpenAlias `network` and `asset` values for completeness.

### Why not support stagenet/testnet? Why only mainnet?

OpenAlias test sending flows can be accomplished without sending transactions, since it is an address and metadata lookup standard. Thus, there is little additional value to be achieved by the increased complexity of supporting networks that are only used for testing purposes.

### Does OpenAlias aim to allow other record standards (ENS, Unstoppable Domains) to directly work with OpenAlias?

No. OpenAlias will not aim to directly support other standards. However, OpenAlias aims to avoid conflicting with other standards.

One long-term goal could be to build a universal library that allows interpreting a variety of standards including OpenAlias and other popular standards.

### Why were _openaliaas-routing records dropped from the OA2 specification?

Despite the added complexity, it did not provide the features that were desired. Allowing a priority per `_openalias-payment` records is simpler *and* more thorough.

## Limitations of OA1

* Since it was created in 2014/2015 before Ethereum and before it was common to have tokens on multiple blockchains, OAv1 does not sensibly allow for passing the network for a given asset. ETH on Ethereum mainnet might be `eth`, but ETH on Polygon might have to be `eth_poly` or similar. This is inelegant.
* Arguably, the length of several key-value pairs are longer than they need to be.
* There is no priority. Suppose someone wants to be paid in USDT, and they prefer to receive it on Ethereum, then failing that, on Polygon.
* OA1 does not attempt to indicate the address type, which might be very useful for certain Bitcoin applications.
* OpenAlias records are not organized into a dedicated OpenAlias section, which may result in clutter.

## Advantages of OA1

* DNS TXT records with DNSSEC remains one of the simplest and most robust ways to handle these alias lookups.
* OA1 includes a version number, which means we can upgrade to a new OAv2 without breaking existing v1 records.
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
