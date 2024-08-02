# OpenAlias v2 Specification

*Not yet adopted. Currently being discussed with the community.*

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

## Proposed OA2 Format

OpenAlias v2 introduces new OpenAlias record types.

### `_openalias-metadata`

`_openalias-metadata` contains various items that are useful across different record types. For example, you can specify a name, image link, social profile links, social profile usernames, or other information.

Example name and image for `donate@openalias.org`:

* TXT name: `_openalias-metadata.donate`
* TXT content: `oa2 name=OpenAlias Project; image=https://openalias.org/image.png`

#### `_openalias-metadata` Key-Value Pairs

* name
* description
* checksum
* image
* twitter
* nostr
* signal
* telegram

#### `image`

This is an optional link to an image file on the ***same*** domain and subdomain as the TXT record. For example:

> image=https://getmonero.org/press-kit/symbols/monero-symbol-on-white-480.png

Wallet developers MUST prohibit image (and other metadata) lookups to links on another domain or subdomain.

### `_openalias-payment`

`_openalias-payment` is the core TXT record name for communicating payment information.

The TXT record name begins with `_openalias-payment`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-payment.`. For `example.openalias.org`, the subdomain would be `_openalias-payment.example`.

The TXT content is:

> oa2 [asset_component] address=[address_component];

Records often appear in these two ways:

> oa2 [asset_network]/[asset_type] address=[address_type]/[address];

> oa2 [asset_network] address=[address];

#### `_openalias-payment` Key-Value Pairs

* address (required)
* amount
* payment_id
* address_signature
* checksum

#### `asset_component`

The `asset_component` is either an `asset_network` and `asset_type`, or an `asset_network`. A forward slash `/` separates the `asset_network` and `asset_type`.

`asset_network` is required. `asset_type` is recommended.

This is a major improvement from OA1. Instead of simply specifying `usdt` as the prefix, recordholders can specify the exact network that they wish to receive USDT on, eg: `eth/usdt`.

Either a nickname can be used for the `network_asset` or the full token ID. For example, the Uniswap token on Ethereum can be represented as either `eth/uni` or `eth/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984`.

#### `address_component`

The `address_component` includes the `address` prefixed by an optional `address_type`. A forward slash `/` separates the `address_type` and `address`.

The `address_type` is an optional (but recommended) identifier for the address type. Example address types might be `p2tr`, `p2wpkh`, `p2sh`, `p2pkh`, `bip352` (silent payments address), `bip47` (PayNym).

#### `checksum`

Including a checksum is optional.

OA1 used CRC32; OA2 uses Adler-32.

> checksum = adler32(concatenate(all_fields_except_checksum))

***Question (primarily for fluffypony): Why use Adler-32?***

### `_openalias-routing`

`_openalias-routing` is an advanced record type for communicating payment priority. Routing records contain an `asset_type` (optional), `asset_network`, and `priority`.

The TXT record name begins with `_openalias-routing`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-routing.`. For `donate.openalias.org`, the subdomain would be `_openalias-routing.donate`.

Priority is a required integer. The lowest number is the highest priority. Each priority value MUST be unique.

Routing records are filtered out if they do not match the `asset_type` or the `asset_network`. The post-filter, remaining records are sorted by priority and selected in priority order.

Example routing records for `example@openalias.org`:

* TXT names: `_openalias-routing.example`
* TXT1 content: `oa2 poly/usdt 10`
* TXT2 content: `oa2 eth/usdt 20`
* TXT3 content: `oa2 eth 30`
* TXT4 content: `oa2 poly 40`

For the four records above:

* If the sender can provide USDT on Ethereum but not Polygon, then the priority `_openalias-payment` record is `eth/usdt`.
* If the sender is providing USDT (on any network), then the priority `_openalias-payment` record is `poly/usdt`.
* If the sender is providing USDC on Ethereum, then the priority `_openalias-payment` record is `eth`.
* If the sender is providing DAI on Polygon, then the priority `_openalias-payment` record is `poly`.

If several `_openalias-routing` records would fit a sending situation and have the same priority value, then throw an error. If a matching payment record is not located, then skip to the next routing record in priority order.

The sender wallet, not the OpenAlias recordholder (recipient), should select which address type to prioritize sending to. Incompatible address types should be removed, and then the wallet can either let the sending user specify their preferred option among the remaining records or a sensible wallet default can be used.

## OA2 Lists

For OA1, there was an expressed interest in maintaining an official list of prefixes, but this never materialized.

For OA2, OpenAlias should publish standardized lists of `asset_type` (for major assets only), `asset_network`, and `address_type`.

OA2 should maintain a list that maps `asset_network` and `asset_type` values to [CAIP-2](https://chainagnostic.org/CAIPs/caip-2) and [CAIP-19](https://chainagnostic.org/CAIPs/caip-19), respectively.

***Question: is there a need to map `asset_network` and `asset_type` to ecosystem lists outside of CAIP-2 and CAIP-19?***

***Question: should OpenAlias maintain a list of key-value pairs for `_openalias-metadata` records?***

## Security Considerations and Requirements

There must be a valid DNSSEC trust chain (RRSIG, DNSKEY, NSEC3), or else the OpenAlias lookup must fail. DNSSEC is much more widely supported than it was when the OA1 standard was created.

## Privacy Considerations and Requirements

When fetching metadata from links, such as an image, this will leak the user's IP address to that server.

Implementations must restrict metadata link lookups to the specific domain and subdomain.

Implementations should consider opt-in user consent before fetching content from links. This can be done through an application setting or requested in each situation.

Implementations should consider proxying link information requests if they already proxy other information for users.

## Example

We will use the example OpenAlias `example@openalias.org` with the following records:

### _openalias-payment.example

> oa2 btc/btc address=bip352:sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v;
> oa2 btc address=1KTexdemPdxSBcG55heUuTjDRYqbC5ZL8H;
> oa2 xmr address=888tNkZrPN6JsEgekjMnABU4TBzc2Dt29EPAvkRxbANsAnjyPbb3iQ1YBRk1UXcdRsiKc9dhwMVgN5S9cQUiyoogDavup3H;
> oa2 eth address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97;
> oa2 poly address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97;
> oa2 base address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97;
> oa2 base/usdc address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97;
> oa2 eth/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97;

### _openalias-routing.example

> oa2 base/usdc 10
> oa2 eth 20
> oa2 poly 30
> oa2 base 40

### _openalias-metadata.example

> oa2 name=OpenAlias Project; image=https://example.openalias.org/image.png; signal=openalias.01;

### Example Wallet Implementation

1. The sender provides `example@openalias.org` as the string that they wish to send their funds to.

2. Optional: fetch the `_openalias-metadata.example` record. If you have implemented any key-value pairs such as `image`, use them as desired. Do not load any content from a different domain and subdomain (if applicable). You might consider requiring explicit user content before fetching links, and warning the user that this will potentially leak their IP address to the server.

3. Determine based on sender context what assets and/or networks that should be reviewed. You should review ALL records that could be used in the context of the sending experience. Make lists with the applicable `asset_network` and `asset_type` values.

4. Fetch all `_openalias-routing.example` records. For each, derive the `asset_network` and `asset_type` that they relate to. Discard all `_openalias-routing.example` records that do not match either the `asset_network` and `asset_type`.

5. Confirm that the domain properly has DENSSEC configured. If it is not properly configured, then throw an error saying that the recipient has not safely configured DNSSEC for OpenAlias.

6. Sort the  `_openalias-routing.example` records by priority (lower number = higher priority). Skip this step if there are no `_openalias-routing.example` records.

7. Fetch all `_openalias-payment.example` records. For each, derive the `asset_network` and `asset_type` that they relate to. Discard all `_openalias-payment.example` records that do not match either the `asset_network` and `asset_type`.

8. Starting with highest priority routing record, search for a matching `_openalias-payment.example` record. If there are no matching records for that priority, then move to the next routing record. If there are no `_openalias-routing.example` records, then use the payment record.

9. If there are several matching records, then select the priority record as follows:

    1. First, filter out all `address_type` instances that are marked incompatible. For example, if a wallet cannot send to a bip352 address, then remove that record. Wallets should check compatibility with the address by seeing if the `address_type` string is supported, or through some other separate address validation logic. If only one record remains, then use that record.

    2. If several records remain, have the user select which address they would like to send to, or implement local wallet logic to prioritize a preferred address type. For example, a wallet may wish to prioritize newer, more efficient, or more private address types by default.

### Example Scenarios

* If the user is sending USDT and the wallet supports the ETH and POLY networks, then the final used payment record should be `oa2 eth address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97`

* If the user is sending BTC and the wallet supports sending to bip352 addresses, then the final used payment record should be `oa2 btc/btc address=bip352:sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v` or a user selection for the two `btc` records.

* If the user is sending BTC and the wallet does NOt support sending to bip352 addresses, then the final used payment record should be `oa2 btc address=1KTexdemPdxSBcG55heUuTjDRYqbC5ZL8H`

* If a user is sending USDC and the wallets supports the ETH and BASE networks, then the final used payment record should be `oa2 base/usdc address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97`.

## FAQ

### Why not use CAIP-2 and CAIP-19 directly for `asset_network` and `asset_type`?

CAIPs references other [namespace](https://namespaces.chainagnostic.org/) standards. For example, the CAIP-2 blockchain identifiers for the following common assets are:

| Blockchain Friendly Name | CAIP-2 | OpenAlias `asset_network` |
| --- | --- | --- |
| Bitcoin Mainnet | `bip122:000000000019d6689c085ae165831e93` | `btc` |
| Monero Mainnet | `monero:418015bb9ae982a1975da7d79277c270` | `xmr` |
| Litecoin Mainnet | `bip122:12a765e31ffd4059bada1e25190f6e98` | `ltc` |

Likewise, CAIP-19 references other [namespaces](https://namespaces.chainagnostic.org/), with `slip144` being the primary namespace outside ecosystem-specific ones. The following example CAIP-19 asset identifiers are:

| Blockchain Friendly Name | CAIP-19 | OpenAlias `asset_network` and `asset_type` |
| --- | --- | --- |
| Uniswap on Ethereum | `eip155:1/erc20:0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` | `eth/uni` or `eth/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` |
| XMR on Monero | `monero:418015bb9ae982a1975da7d79277c270/slip44:128` | `xmr/xmr` |
| BTC on Bitcoin | `bip122:000000000019d6689c085ae165831e93/slip44:0` | `btc/btc` |
| LTC on Litecoin | `bip122:12a765e31ffd4059bada1e25190f6e98/slip44:2` | `ltc/ltc` |

Including CAIP-2 and CAIP-19 in their entirety is overkill for OpenAlias purposes. Supporting native use of CAIP-2 and CAIP-19 in OpenAlias records would add these [namespaces](https://namespaces.chainagnostic.org/) as a dependency. The benefits of allowing CAIP natively in OpenAlias seems to create more work and complexity overall; however, this could be reconsidered if CAIP is widely adopted in nearly all wallets.

Nevertheless, CAIP-2 and CAIP-19 are useful for mapping OpenAlias `asset_network` and `asset_type` values for completeness.

### Why not support stagenet/testnet? Why only mainnet?

OpenAlias test sending flows can be accomplished without sending transactions, since it is an address and metadata lookup standard. Thus, there is little additional value to be achieved by the increased complexity of supporting networks that are only used for testing purposes.

### Does OpenAlias aim to allow other record standards (ENS, Unstoppable Domains) to directly work with OpenAlias?

No. OpenAlias will not aim to directly support other standards. However, OpenAlias aims to avoid conflicting with other standards.

One long-term goal could be to build a universal library that allows interpreting a variety of standards including OpenAlias and other popular standards.
