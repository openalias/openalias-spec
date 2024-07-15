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

## Avoiding Conflicting Standards

OA1 and OA2 do not need to be compatible with every other alias standard, but we should avoid conflicting with them where possible. Some notable ones are:

* Ethereum Name Service (ENS)
* Namecoin
* Unstoppable Domains
* https://github.com/bitcoin/bips/pull/1551

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

Wallet developers MUST prohibit image lookups on another domain or subdomain.

### `_openalias-payment`

`_openalias-payment` is the core TXT record name for communicating payment information.

The TXT record name begins with `_openalias-payment`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-payment.`. For `example.openalias.org`, the subdomain would be `_openalias-payment.example`.

The TXT content is:

> oa2 [asset_component] address=[address_component];

Records often appear in these two ways:

> oa2 [asset_ticker]:[asset_network] address=[address_type]:[address];

> oa2 [asset_network] address=[address];

#### `_openalias-payment` Key-Value Pairs

* address (required)
* amount
* payment_id
* address_signature
* checksum

#### `asset_component`

The `asset_component` is either an `asset_ticker` and `asset_network`, or an `asset_network`. A colon separates the `asset_ticker` and `asset_network`.

`asset_network` is required. `asset_ticker` is recommended.

This is a major improvement in OA. Instead of simply specifying `usdt` as the prefix, recordholders can specify the exact network that they wish to receive USDT on, eg: `usdt:eth`.

#### `address_component`

The `address_component` includes the `address` prefixed by an optional `address_type`. A colon separates the `address_type` and `address`.

The `address_type` is an optional (but recommended) identifier for the address type. Example address types might be `p2tr`, `p2wpkh`, `p2sh`, `p2pkh`, `bip352` (silent payments address), `bip47` (PayNym).

### `_openalias-routing`

`_openalias-routing` is an advanced record type for communicating payment priority. Routing records contain an `asset_ticker` (optional), `asset_network`, and `priority`.

The TXT record name begins with `_openalias-routing`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-routing.`. For `donate.openalias.org`, the subdomain would be `_openalias-routing.donate`.

Priority is a required integer. The lowest number is the highest priority. Each priority value MUST be unique.

Routing records are filtered out if they do not match the `asset_ticker` or the `asset_network`. The post-filter, remaining records are sorted by priority and selected in priority order.

Example routing records for `example@openalias.org`:

* TXT names: `_openalias-routing.example`
* TXT1 content: `oa2 usdt:poly 10`
* TXT2 content: `oa2 usdt:eth 20`
* TXT3 content: `oa2 eth 30`
* TXT4 content: `oa2 poly 40`

For the four records above:

* If the sender can provide USDT on Ethereum but not Polygon, then the priority `_openalias-payment` record is `usdt:eth`.
* If the sender is providing USDT (on any network), then the priority `_openalias-payment` record is `usdt:poly`.
* If the sender is providing USDC on Ethereum, then the priority `_openalias-payment` record is `eth`.
* If the sender is providing DAI on Polygon, then the priority `_openalias-payment` record is `poly`.

If several `_openalias-routing` records would fit a sending situation and have the same priority value, then throw an error. If a matching payment record is not located, then skip to the next routing record in priority order.

The sender wallet, not the OpenAlias recordholder (recipient), should select which address type to prioritize sending to. Incompatible address types should be removed, and then the wallet can either let the sending user specify their preferred option among the remaining records or a sensible wallet default can be used.

## OA2 Lists

For OA1, there was an expressed interest in maintaining an official list of prefixes, but this never materialized.

For OA2, OpenAlias should publish standardized lists of `asset_ticker` (for major assets only), `asset_network`, and `address_type`.

***Question: what format should these lists be published in, for them to be most useful to ecosystem developers?***

***Question: is it necessary to standardize a list for `asset_ticker`, or are lists for `asset_network` and `address_type` sufficient?***

***Question: should OpenAlias maintain key-value pairs for `_openalias-metadata` records?***

## Example

We will use the example OpenAlias `example@openalias.org` with the following records:

### _openalias-payment.example

> oa2 btc:btc address=bip352:sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v
> oa2 btc address=1KTexdemPdxSBcG55heUuTjDRYqbC5ZL8H
> oa2 xmr address=888tNkZrPN6JsEgekjMnABU4TBzc2Dt29EPAvkRxbANsAnjyPbb3iQ1YBRk1UXcdRsiKc9dhwMVgN5S9cQUiyoogDavup3H
> oa2 eth address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97
> oa2 poly address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97
> oa2 base address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97
> oa2 usdc:base address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97

### _openalias-routing.example

> oa2 usdc:base 10
> oa2 eth 20
> oa2 poly 30
> oa2 base 40

### _openalias-metadata.example

> oa2 name=OpenAlias Project; image=https://example.openalias.org/image.png; signal=openalias.01;

### Example Wallet Implementation

1. The sender provides `example@openalias.org` as the string that they wish to send their funds to.

2. Optional: fetch the `_openalias-metadata.example` record. If you have implemented any key-value pairs such as `image`, use them as desired.

3. Determine based on sender context what assets and/or networks that should be reviewed. You should review ALL records that could be used in the context of the sending experience. Make lists with the applicable `asset_ticker` and `asset_network` values.

4. Fetch all `_openalias-routing.example` records. For each, derive the `asset_ticker` and `asset_network` that they relate to. Discard all `_openalias-routing.example` records that do not match either the `asset_ticker` or `asset_network`.

5. Sort the  `_openalias-routing.example` records by priority (lower number = higher priority). Skip this step if there are no `_openalias-routing.example` records.

6. Fetch all `_openalias-payment.example` records. For each, derive the `asset_ticker` and `asset_network` that they relate to. Discard all `_openalias-payment.example` records that do not match either the `asset_ticker` or `asset_network`.

7. Starting with highest priority routing record, search for a matching `_openalias-payment.example` record. If there are no matching records for that priority, then move to the next routing record. If there are no `_openalias-routing.example` records, then use the payment record.

8. If there are several matching records, then select the priority record as follows:

    1. First, filter out all `address_type` instances that are marked incompatible. For example, if a wallet cannot send to a bip352 address, then remove that record. Wallets should check compatibility with the address by seeing if the `address_type` string is supported, or through some other separate address validation logic. If only one record remains, then use that record.

    2. If several records remain, have the user select which address they would like to send to, or implement local wallet logic to prioritize a preferred address type. For example, a wallet may wish to prioritize newer, more efficient, or more private address types by default.

### Example Scenarios

* If the user is sending USDT and the wallet supports the ETH and POLY networks, then the final used payment record should be `oa2 eth address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97`

* If the user is sending BTC and the wallet supports sending to bip352 addresses, then the final used payment record should be `oa2 btc:btc address=bip352:sp1qqfk0ag4gmq87agdy8lawrlt2mf3p8myhkuxgp5s7kdck4ywwg7mjjqc2wmmtfddvevmjnlv4klmgsx4g79rr998d20r5vmxera5f2a54nu5h496v` or a user selection for the two `btc` records.

* If the user is sending BTC and the wallet does NOt support sending to bip352 addresses, then the final used payment record should be `oa2 btc address=1KTexdemPdxSBcG55heUuTjDRYqbC5ZL8H`

* If a user is sending USDC and the wallets supports the ETH and BASE networks, then the final used payment record should be `oa2 usdc:base address=0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97`.
