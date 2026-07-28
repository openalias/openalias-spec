/// openalias — resolve OpenAlias v2 records (Dart).
///
/// A small, readable Dart port of the Python example. It mirrors the same
/// structure: alias normalization, DNSSEC-validated TXT resolution, key-value
/// parsing, typed payment records, and native-asset lookup.
///
/// Trust model
/// -----------
/// DNS answers are validated to the DNS root and the resolver is not trusted —
/// exactly like the Python example. Pure Dart has no practical local DNSSEC
/// validator, so (as Skylight Wallet does) the validating lookup is performed
/// by a small Rust helper in `native/` and called here over FFI. The helper
/// returns only records proven `Secure`; anything else fails closed.
///
/// Build the helper first: `cd native && cargo build --release`.
library;

import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';

const String paymentPrefix = '_openalias-payment';
const String metadataPrefix = '_openalias-metadata';

// --- errors ------------------------------------------------------------------

class OpenAliasException implements Exception {
  final String message;
  OpenAliasException(this.message);
  @override
  String toString() => message;
}

/// The input is a raw address, not an OpenAlias.
class NotAnAlias extends OpenAliasException {
  NotAnAlias(String message) : super(message);
}

/// The answer could not be DNSSEC-validated and must not be trusted.
class InsecureLookup extends OpenAliasException {
  InsecureLookup(String message) : super(message);
}

/// The DNS lookup itself failed (network error, SERVFAIL, timeout, ...).
class LookupFailed extends OpenAliasException {
  LookupFailed(String message) : super(message);
}

// --- native library (DNSSEC-validated TXT lookup; see native/) ---------------

typedef _SecureTxtNative = Pointer<Utf8> Function(Pointer<Utf8>);
typedef _SecureTxt = Pointer<Utf8> Function(Pointer<Utf8>);
typedef _FreeNative = Void Function(Pointer<Utf8>);
typedef _Free = void Function(Pointer<Utf8>);

/// Path to the compiled native helper; reassign to override the default.
String nativeLibraryPath = _defaultNativeLibraryPath();

String _defaultNativeLibraryPath() {
  final dir = File.fromUri(Platform.script).parent.path;
  final base = '$dir/native/target/release';
  if (Platform.isMacOS) return '$base/libopenalias_native.dylib';
  if (Platform.isWindows) return '$base/openalias_native.dll';
  return '$base/libopenalias_native.so';
}

class _Native {
  final _SecureTxt secureTxt;
  final _Free free;
  _Native(this.secureTxt, this.free);

  static _Native? _cached;
  static _Native get instance => _cached ??= _open();

  static _Native _open() {
    final lib = DynamicLibrary.open(nativeLibraryPath);
    return _Native(
      lib.lookupFunction<_SecureTxtNative, _SecureTxt>('oa_secure_txt'),
      lib.lookupFunction<_FreeNative, _Free>('oa_free'),
    );
  }
}

/// Resolve `name`'s TXT records, DNSSEC-validated by the native helper.
///
/// Returns each record as a single string (its DNS character-strings already
/// concatenated). Throws [InsecureLookup] if the answer is not DNSSEC-secure,
/// or [LookupFailed] if the lookup failed.
List<String> _secureTxt(String name) {
  final native = _Native.instance;
  final arg = name.toNativeUtf8();
  final Pointer<Utf8> resultPtr;
  try {
    resultPtr = native.secureTxt(arg);
  } finally {
    malloc.free(arg);
  }
  if (resultPtr == nullptr) {
    throw LookupFailed('$name: native resolver returned null');
  }
  final String result;
  try {
    result = resultPtr.toDartString();
  } finally {
    native.free(resultPtr); // buffer was allocated by Rust; free it there
  }

  final newline = result.indexOf('\n');
  final status = newline < 0 ? result : result.substring(0, newline);
  final body = newline < 0 ? '' : result.substring(newline + 1);
  switch (status) {
    case 'ok':
      return body.isEmpty ? <String>[] : body.split('\n');
    case 'insecure':
      throw InsecureLookup('$name: $body');
    default:
      throw LookupFailed('$name: $body');
  }
}

// --- alias normalization -----------------------------------------------------

String normalize(String alias) {
  alias = alias.trim();
  while (alias.endsWith('.')) {
    alias = alias.substring(0, alias.length - 1);
  }
  if (alias.isEmpty) throw NotAnAlias('empty input');
  if ('@'.allMatches(alias).length > 1) {
    throw OpenAliasException("malformed alias '$alias': more than one '@'");
  }
  alias = alias.replaceFirst('@', '.');
  if (!alias.contains('.')) {
    throw NotAnAlias("'$alias' looks like a raw address, not an alias");
  }
  final labels = alias.split('.');
  if (labels.any((l) => l.isEmpty)) {
    throw OpenAliasException("malformed alias '$alias': contains an empty label");
  }
  // NOTE: internationalized (non-ASCII) domains must first be converted to their
  // A-label (Punycode) form. This example expects ASCII input and does not bundle
  // a Punycode encoder (the Python example uses the standard library for this).
  return alias;
}

// --- record parsing ----------------------------------------------------------

final RegExp _keyChars = RegExp(r'^[a-z0-9_]+$');

/// Parse one TXT record into a {key: value} map, per the OA2 Key-Value Encoding
/// rules. Returns null for a record with a malformed or repeated key.
Map<String, String>? parseRecord(String text) {
  final fields = <String, String>{};
  for (var pair in text.split(';')) {
    pair = pair.trim(); // tolerate the optional space and a trailing ';'
    if (pair.isEmpty) continue;
    final eq = pair.indexOf('='); // only the first '=' is significant
    if (eq < 0) return null;
    final key = pair.substring(0, eq).trim().toLowerCase();
    final value = pair.substring(eq + 1);
    if (!_keyChars.hasMatch(key)) return null;
    if (fields.containsKey(key)) return null;
    fields[key] = value;
  }
  return fields;
}

/// Resolve every OA2 record under `prefix` for `alias` as raw {key: value} maps.
List<Map<String, String>> records(String alias, String prefix) {
  final name = '$prefix.${normalize(alias)}';
  final out = <Map<String, String>>[];
  for (final text in _secureTxt(name)) {
    final fields = parseRecord(text);
    if (fields != null && fields['oa_version'] == '2') out.add(fields);
  }
  return out;
}

// --- payment records ---------------------------------------------------------

class PaymentRecord {
  final String network;
  final String address;
  final String? asset;
  final String? addressType;
  final int? priority;
  final String? amount; // decimal string in the asset's standard units
  final String? memo;
  final Map<String, String> fields; // every raw pair, including unknown keys

  PaymentRecord({
    required this.network,
    required this.address,
    this.asset,
    this.addressType,
    this.priority,
    this.amount,
    this.memo,
    required this.fields,
  });

  /// The asset being paid; an omitted asset means the network's native asset.
  String get effectiveAsset => asset ?? network;
}

PaymentRecord? _paymentFromFields(Map<String, String> f) {
  final network = f['network'];
  final address = f['address'];
  if (network == null || network.isEmpty || address == null || address.isEmpty) {
    return null; // network and address are required
  }
  final priority = f['priority'];
  return PaymentRecord(
    network: network,
    address: address,
    asset: f['asset'],
    addressType: f['address_type'],
    priority: priority == null ? null : int.tryParse(priority),
    amount: f['amount'],
    memo: f['memo'],
    fields: f,
  );
}

/// Resolve payment records for `alias`, most-preferred first (by `priority`;
/// a record with no priority sorts last).
List<PaymentRecord> payments(String alias) {
  final found = <PaymentRecord>[];
  for (final f in records(alias, paymentPrefix)) {
    final record = _paymentFromFields(f);
    if (record != null) found.add(record);
  }
  found.sort((a, b) => (a.priority ?? 1 << 30).compareTo(b.priority ?? 1 << 30));
  return found;
}

/// Resolve the first `_openalias-metadata` record for `alias`, or null.
Map<String, String>? metadata(String alias) {
  final found = records(alias, metadataPrefix);
  return found.isEmpty ? null : found.first;
}

// --- native asset ------------------------------------------------------------

/// Path to the OA2 network list; reassign to override the default.
String networkListPath =
    '${File.fromUri(Platform.script).parent.path}/../../oa2-lists/network.csv';

Map<String, String>? _nativeAssets;

/// The `asset` id of `network`'s native asset, per the OA2 network list, or null
/// if the network is unknown or lists no native asset.
String? nativeAsset(String network) {
  _nativeAssets ??= _loadNativeAssets();
  return _nativeAssets![network];
}

Map<String, String> _loadNativeAssets() {
  final map = <String, String>{};
  final lines = File(networkListPath).readAsLinesSync();
  if (lines.isEmpty) return map;
  final header = lines.first.split(',');
  final netIdx = header.indexOf('OpenAlias network');
  final nativeIdx = header.indexOf('Network Native asset');
  if (netIdx < 0 || nativeIdx < 0) return map;
  for (final line in lines.skip(1)) {
    if (line.trim().isEmpty) continue;
    final cols = line.split(',');
    if (cols.length <= netIdx || cols.length <= nativeIdx) continue;
    final net = cols[netIdx].trim();
    final native = cols[nativeIdx].trim();
    if (net.isNotEmpty && native.isNotEmpty) map[net] = native;
  }
  return map;
}

/// True if `record` pays its network's native asset (asset omitted, or equal to
/// the network's recorded native asset).
bool isNative(PaymentRecord record) =>
    record.asset == null || record.asset == nativeAsset(record.network);
