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

### `_openalias-metadata `

`_openalias-metadata` contains various items that are useful across different record types. For example, you can specify a name, image link, social profile links, social profile usernames, or other information.

Example name and image for `donate@openalias.org`:

* TXT name: `_openalias-metadata.donate`
* TXT content: `oa2 name=OpenAlias Project; image=https://openalias.org/image.png`

#### `_openalias-metadata ` Key-Value Pairs

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

The TXT record name begins with `_openalias-payment`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-payment.`. For `donate.openalias.org`, the subdomain would be `_openalias-payment.donate`.

The TXT content is:

> oa2 [asset_ticker]:[asset_network] address=[address_type]:[address];

#### `_openalias-payment` Key-Value Pairs

* address (required)
* amount
* payment_id
* address_signature
* checksum

#### `asset_ticker` and `asset_network`

One of `asset_ticker` or `asset_network` is required. Both are recommended, even for networks that do not support additional tokens.

This is a major improvement in OA. Instead of simply specifying `usdt` as the prefix, recordholders can specify the exact network that they wish to receive USDT on, eg: `usdt:eth`.

#### `address_type`

This is an optional (but recommended) identifier for the address type. Example address types might be `p2tr`, `p2wpkh`, `p2sh`, `p2pkh`, `bip352` (silent payments address), `bip47` (PayNym).

### `_openalias-routing`

`_openalias-routing` is an advanced record type for communicating payment priority.

The TXT record name begins with `_openalias-routing`. Records placed under that name will act as root records. Subdomain records are possible by affixing that subdomain after `_openalias-routing.`. For `donate.openalias.org`, the subdomain would be `_openalias-routing.donate`.

Priority is an optional integer. The lowest number is most preferred. If the priority is not provided, then the record will have a lower priority than other matching TXT records with a priority.

Priority is first conducted among exact matches of `asset_ticker`, and then `asset_network` only if there is no match for the `asset_ticker`. 

Example routing records for `donate@openalias.org`:

* TXT names: `_openalias-routing.donate`
* TXT1 content: `oa2 usdt:poly 20`
* TXT2 content: `oa2 usdt:eth 30`
* TXT3 content: `oa2 :eth 10`
* TXT4 content: `oa2 :poly`

For the four records above:

* If the sender can only provide USDT on Ethereum, then a `usdt:eth` record should be fetched from `_openalias-payment`.
* If the sender is providing USDT (on any network), then a `usdt:poly` record should be fetched from `_openalias-payment`.
* If the sender is providing USDC on Ethereum, then a `:eth` record should be fetched from `_openalias-payment`.
* If the sender is providing DAI on Polygon, then a `:poly` record should be fetched from `_openalias-payment`.

***Question: should we allow re-use of the same integer multiple times to signal to the sender an indifference between receive types?***

## OA2 Lists

For OA1, there was an expressed interest in maintaining an official list of prefixes, but this never materialized.

For OA2, OpenAlias should publish standardized lists of `asset_ticker` (for major assets only), `asset_network`, and `address_type`.

***Question: what format should these lists be published in, for them to be most useful to ecosystem developers?***

***Question: is it necessary to standardize a list for `asset_ticker`, or are lists for `asset_network` and `address_type` sufficient?***

***Question: should OpenAlias maintain key-value pairs for `_openalias-metadata` records?***
