# OpenAlias v2 — Dart example

A Dart port of the [Python example](../python), with the same structure:
alias normalization, DNSSEC-validated TXT resolution, key-value parsing, typed
payment records, native-asset lookup, and wallet-style selection.

## Trust model

DNS answers are validated to the DNS root and the resolver is **not** trusted —
the same model as the Python example. Pure Dart has no practical local DNSSEC
validator, so (exactly as [Skylight Wallet](https://github.com/MAGICGrants/skylight-wallet)
does) that step runs in a small **Rust helper** under [`native/`](native/) —
built on [hickory](https://github.com/hickory-dns/hickory-dns) — and is called
from Dart over FFI. The helper turns on hickory's DNSSEC validation and
additionally requires every record to be proven `Secure`, so an unsigned domain
fails closed rather than being accepted.

## Build the native helper

```sh
cd native
cargo build --release
cd ..
```

This produces `native/target/release/libopenalias_native.{so,dylib,dll}`, which
`openalias.dart` loads at runtime (override `nativeLibraryPath` to point
elsewhere).

## Run

```sh
dart pub get
dart run wallet.dart donate@openalias.org
dart run fetch_all_records.dart donate@openalias.org
```

## Files

- [`openalias.dart`](openalias.dart) — the library: FFI to the native resolver,
  OA2 record parsing, typed `PaymentRecord`, native-asset lookup, and selection.
- [`wallet.dart`](wallet.dart) — resolve an alias, pick the highest-priority
  supported payment record, and confirm the address before sending.
- [`fetch_all_records.dart`](fetch_all_records.dart) — print every OA2 payment
  and metadata record for an alias.
- [`native/`](native/) — the Rust helper doing DNSSEC-validated TXT resolution.

## Notes

- The lookup is synchronous for simplicity; a real app should run it off the UI
  isolate (Skylight uses a background isolate).
- Internationalized domains must be pre-converted to their A-label (Punycode)
  form; this example expects ASCII input (the Python example converts them via
  the standard library).
