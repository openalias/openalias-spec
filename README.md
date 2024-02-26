# OpenAlias Spec

This GitHub repository is the home for the official OpenAlias specifications.

The OpenAlias v2 Specification is currently being discussed. Please review the pull requests and issues, and join our [Matrix](https://matrix.to/#/#openalias:matrix.org) or Libera IRC (#openalias) channel for further discussion.

## What is OpenAlias?

OpenAlias (https://openalias.org) seeks to simplify aliasing amidst a rapidly shifting technology climate. Users are trying to cross the bridge to private and cryptographically secure infrastructure and systems, but many of them have just barely started remembering the email addresses of their friends and family.

As part of the ongoing development of the [Monero cryptocurrency project](https://getmonero.org), we asked ourselves: how can we simplify payments for users unfamiliar with cryptocurrency? Monero stealth addresses are at least 95 characters long - memorising them is not an option, and asking someone to send a payment to <95-character-string> is only going to lead to confusion.

At its most basic, OpenAlias is a TXT DNS record on a FQDN (fully qualified domain name). By combining this with DNS-related technologies we have created an aliasing standard that is extensible for developers, intuitive and familiar for users, and can interoperate with both centralised and decentralised domain systems.

## How is it superior to other aliasing systems?

Typical aliasing systems are simple key-value stores. A cryptocurrency may, for instance, have an aliasing system that lets you (through the process of mining) declare that the alias Bob is equal to <95-character-string>. This has two major pitfalls for end-users. Firstly, it makes it the responsibility of that cryptocurrency to resolve issues or alias disputes. For instance, if a user loses their private keys and want to continue using that alias, there needs to be a mechanism in place for that, otherwise you end up with dead aliases and users have the hassle of having to update everyone that they have a new alias. The second problem is that it doesn't actually solve anything. Once the first few Bob-derived aliases are taken, users end up resorting to things like Bob1979-awesomesauce324, which means that the end-user still has to have that written down in an address book somewhere.

## Who created OpenAlias?

The idea of a DNS-based alias system is not new, and has been suggested on more than one occassion. The groundwork for OpenAlias was initially done by Riccardo "fluffypony" Spagni and Naphex, formerly of btcXchange.ro. Many months after this initial gem of an idea was born Riccardo, along with the rest of the Monero core team, fleshed it out into a practical and extensible standard. A special thanks goes to Tom Winget, who created the first OpenAlias client implementation in Monero Core.

## What OpenAlias implementations exist?

The Monero core team, and other contributors, are actively adding new OpenAlias implementations. To that end, there are currently five implementations:

* [Electrum, lightweight Bitcoin wallet](https://electrum.org/) (from 2.0 onwards)
* [MyMonero, a web-based Monero account/wallet management system](https://mymonero.com/)
* [Monero Core, including the simplewallet and rpcwallet applications](https://getmonero.org/)
* [Coin.Space, a web-based Bitcoin and Litecoin wallet](https://coin.space/)
* [openalias.rs, a command-line tool and Rust library for looking up and parsing OpenAliases](https://github.com/nabijaczleweli/openalias.rs)

## What is the end-user-side process?

OpenAlias can be used for anything, but our primary use-case is to simplify cryptocurrency payments. Users are already familiar with systems like PayPal that let you send a payment to an email address. Thus, to the end user this should be no less intuitive. In order to make the paradigm truly familiar for the end user, OpenAlias allows for the user to enter either just the FQDN (eg. example.openalias.org) or an email-style address that is translated to an FQDN (eg. example@openalias.org)

Workflow:

1. user wants to send a payment to donate.getmonero.org
2. user visually confirms the resulting address is as expected
3. payment is made to the address

## What is the application-side process?

Applications should, at a minimum, implement the following workflow.

Workflow:
1. if the value entered contains an @ character, replace it with a . (period) character to allow for email-style addressing
2. check that the value entered contains a . (period) character, if not then it is an address and not an FQDN
3. fetch all of the TXT records for the FQDN, retry at least 3 times on failure, handle an overall failure in the lookup
4. step through each of the TXT records and make sure we have the oa1 (OpenAlias version 1) prefix followed by the prefix for our application (oa1:xmr in our example), break on the first match (ignoring later matches unless your application specifically supports handling multiple records)
5. extract the recipient_address from the parsed data
6. check if we have a valid DNSSEC trust chain (RRSIG, DNSKEY, NSEC3), if not then alert the user that it is potentially untrusted, continue if the user agrees
7. confirm the validity of the address with the user

## How do we prevent the user's lookups from leaking?

In order to ensure that lookups do not betray the user's privacy it is best to implement DNSCrypt from OpenDNS, and force resolution via a DNSCrypt-compatible resolver. Dependent on your use-case, you may choose to bake DNSCrypt into your software, or bundle dnscrypt-proxy along with your application.

There are only a handful of DNSCrypt compatible resolvers worldwide, and fewer still that additionally support DNSSEC validation, support Namecoin resolution, and don't log DNS requests. Additional DNS resolvers that meet these criteria will be launched and operated by OpenAlias and by contributors in the coming months. In order to make your life easier, you can get a list of available resolvers that meet all these criteria by fetching the TXT records from any of the following domains:

* resolvers.openalias.org
* resolvers.openalias.ch
* resolvers.openalias.se
* resolvers.openalias.li

The TXT records consist of host:port=providername=pubkey, allowing you to connect to their DNSCrypt resolver using these details. These resolver records will be maintained, and if a malicious resolver is found it will be removed. It is, therefore, prudent to poll this list regularly within the application, either on-request or at least once every 24 hours.

## How are the TXT records constructed?

This varies by OA version. Please see the table below:

| OpenAlias Version | Specification Link |
| --- | --- |
| OA1 | [Link](/oa1.md) |
| OA2 | [Link](/oa2.md) |

## How can I support the OpenAlias project?

In order to simplify implementation for developers, the Monero Project is writing sample implementations and libraries for various languages. Additionally, OpenAlias will run open and free DNS servers that support Namecoin, DNSSEC, and DNSCrypt. If you are a developer and wish to submit or contribute code, please feel free to do so.

If you would like to support this ongoing effort and help us cover the costs, please consider donating to the Monero Project either via Monero:

> 46BeWrHpwXmHDpDEUmZBWZfoQpdc6HaERCNmx1pEYL2rAcuwufPN9rXHHtyUA4QVy66qeFQkn6sfK8aHYjA3jk3o1Bv16em

or via Bitcoin:

> 1FhnVJi2V1k4MqXm2nHoEbY5LV7FPai7bb

If you use an OpenAlias compatible client, both of these donation addresses are available on openalias.org and/or donate.getmonero.org.

## What about contacting you or the community?

Matrix: #openalias:matrix.org

Libera IRC: #openalias
