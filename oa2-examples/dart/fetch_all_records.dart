// Print every OpenAlias v2 record published for an alias.
//
// A Dart port of the Python fetch-all example. Requires the native helper to be
// built first: `cd native && cargo build --release`.
//
// Usage:
//   dart run fetch_all_records.dart donate@openalias.org

import 'dart:io';

import 'openalias.dart' as oa;

void main(List<String> args) {
  if (args.length != 1) {
    stderr.writeln('usage: dart run fetch_all_records.dart <alias>   e.g. donate@openalias.org');
    exit(1);
  }
  final alias = args[0];

  final String fqdn;
  try {
    fqdn = oa.normalize(alias);
  } on oa.NotAnAlias catch (e) {
    print(e);
    exit(1);
  }

  print('$alias  ->  $fqdn\n');

  for (final prefix in [oa.paymentPrefix, oa.metadataPrefix]) {
    final name = '$prefix.$fqdn';
    try {
      final found = oa.records(alias, prefix);
      if (found.isEmpty) {
        print('$name: no OpenAlias v2 records\n');
        continue;
      }
      print('$name: ${found.length} record(s)');
      for (final fields in found) {
        fields.forEach((key, value) => print('    $key = $value'));
        print('');
      }
    } on oa.InsecureLookup catch (e) {
      print('$name: REFUSED — $e\n');
    } on oa.LookupFailed catch (e) {
      print('$name: lookup failed — $e\n');
    }
  }
}
