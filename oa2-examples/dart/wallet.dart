// Resolve an OpenAlias and pay the highest-priority address this wallet supports.
//
// A Dart port of the Python wallet example. Requires the native helper to be
// built first: `cd native && cargo build --release`.
//
// Usage:
//   dart run wallet.dart donate@openalias.org

import 'dart:io';

import 'openalias.dart' as oa;

// What this wallet can pay, as (network, asset) pairs:
//   (net, null)  -> only the network's native asset
//   (net, 'sym') -> one specific asset on that network
//   (net, '*')   -> any asset on that network
const supported = <(String, String?)>{
  ('btc', null), // native BTC only
  ('xmr', null), // native XMR only
  ('eth', '*'), // any asset on Ethereum (ETH and all tokens)
  ('trx', 'usdt'), // only USDT on Tron
};

bool isSupported(oa.PaymentRecord record) {
  if (supported.contains((record.network, '*'))) return true;
  // Collapse a native-asset payment to null so it matches a (net, null) entry,
  // using the OA2 network list's native-asset mapping.
  final asset = oa.isNative(record) ? null : record.asset;
  return supported.contains((record.network, asset));
}

void main(List<String> args) {
  if (args.length != 1) {
    stderr.writeln('usage: dart run wallet.dart <alias>   e.g. donate@openalias.org');
    exit(1);
  }
  final alias = args[0];

  final List<oa.PaymentRecord> found;
  try {
    found = oa.payments(alias);
  } on oa.NotAnAlias catch (e) {
    print(e);
    exit(1);
  } on oa.InsecureLookup catch (e) {
    print('Refusing an unauthenticated result: $e');
    exit(1);
  } on oa.LookupFailed catch (e) {
    print('Lookup failed: $e');
    exit(1);
  }

  if (found.isEmpty) {
    print('No OpenAlias v2 payment records for $alias.');
    exit(1);
  }

  final payable = found.where(isSupported).toList(); // already priority-sorted
  if (payable.isEmpty) {
    final offered = (found.map((r) => r.network).toSet().toList()..sort()).join(', ');
    print('$alias accepts $offered; this wallet supports none of them.');
    exit(1);
  }

  final chosen = payable.first;

  String? name;
  try {
    name = oa.metadata(alias)?['name'];
  } on oa.OpenAliasException {
    // metadata is optional and must never block a payment
  }

  print('Paying ${name ?? alias}');
  print('  network:      ${chosen.network}');
  if (chosen.asset != null) print('  asset:        ${chosen.asset}');
  if (chosen.addressType != null) print('  address type: ${chosen.addressType}');
  print('  address:      ${chosen.address}');
  if (chosen.amount != null) print('  amount:       ${chosen.amount} ${chosen.effectiveAsset}');
  if (chosen.memo != null) print('  memo:         ${chosen.memo}');

  stdout.write('\nSend to this address? [y/N] ');
  final answer = stdin.readLineSync()?.trim().toLowerCase();
  if (answer == 'y') {
    print('... (the wallet would build and broadcast the transaction here)');
  } else {
    print('Cancelled.');
  }
}
