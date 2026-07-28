//! Native helper for the Dart OpenAlias example.
//!
//! Resolves DNS TXT records with **local DNSSEC validation** and exposes the
//! result over a tiny C FFI for Dart to call. This mirrors the trust model of
//! the Python example and of Skylight Wallet: the resolver used to fetch the
//! records is not trusted — every signature is validated in-process (by
//! hickory, against its built-in root trust anchor), and anything that does not
//! validate fails closed.
//!
//! FFI surface:
//!   char* oa_secure_txt(const char* name);  // caller frees with oa_free
//!   void  oa_free(char* ptr);
//!
//! `oa_secure_txt` returns a newline-delimited string. The first line is a
//! status word; the remaining lines (if any) are the TXT records, one per line,
//! each already concatenated from its DNS character-strings:
//!   "ok\n<record>\n<record>..."   validated (zero or more records)
//!   "insecure\n<message>"          answer was not DNSSEC-validated (fail closed)
//!   "error\n<message>"             lookup failed (network, SERVFAIL, ...)

use std::ffi::{CStr, CString};
use std::os::raw::c_char;

use hickory_resolver::proto::rr::rdata::TXT;
use hickory_resolver::proto::rr::{RData, RecordType};
use hickory_resolver::TokioResolver;

enum Outcome {
    Ok(Vec<String>),
    Insecure(String),
    Failed(String),
}

fn concat_txt(txt: &TXT) -> String {
    // A TXT record is one or more character-strings; concatenate them in order.
    let mut s = String::new();
    for chunk in txt.txt_data() {
        s.push_str(&String::from_utf8_lossy(chunk));
    }
    s
}

fn resolve(name: &str) -> Outcome {
    let rt = match tokio::runtime::Builder::new_current_thread().enable_all().build() {
        Ok(rt) => rt,
        Err(e) => return Outcome::Failed(e.to_string()),
    };

    rt.block_on(async move {
        // Build a resolver from the system configuration and turn on local
        // DNSSEC validation (fail closed on any validation failure).
        let resolver = match TokioResolver::builder_tokio() {
            Ok(mut builder) => {
                builder.options_mut().validate = true;
                builder.build()
            }
            Err(e) => return Outcome::Failed(e.to_string()),
        };

        match resolver.lookup(name.to_string(), RecordType::TXT).await {
            Ok(lookup) => {
                let mut out = Vec::new();
                for record in lookup.record_iter() {
                    if let RData::TXT(txt) = record.data() {
                        // OpenAlias requires a DNSSEC-validated answer. hickory's
                        // `validate` only rejects *bogus* answers; an unsigned
                        // domain still returns records proven Insecure. Accept
                        // only records proven Secure — fail closed otherwise.
                        if !record.proof().is_secure() {
                            return Outcome::Insecure(format!(
                                "{name}: TXT answer is not DNSSEC-secure (proof: {:?})",
                                record.proof()
                            ));
                        }
                        out.push(concat_txt(txt));
                    }
                }
                Outcome::Ok(out)
            }
            Err(err) => {
                if err.is_no_records_found() {
                    Outcome::Ok(Vec::new())
                } else {
                    // With validate = true, a signature/chain failure surfaces
                    // as a resolve error; treat those as "insecure" (fail closed)
                    // and everything else as a plain lookup failure.
                    let msg = err.to_string();
                    let lower = msg.to_lowercase();
                    if lower.contains("dnssec")
                        || lower.contains("proof")
                        || lower.contains("bogus")
                        || lower.contains("insecure")
                    {
                        Outcome::Insecure(msg)
                    } else {
                        Outcome::Failed(msg)
                    }
                }
            }
        }
    })
}

/// Resolve `name`'s TXT records with local DNSSEC validation. See the module
/// docs for the return format. The caller owns the returned buffer and must
/// release it with [`oa_free`].
#[no_mangle]
pub extern "C" fn oa_secure_txt(name: *const c_char) -> *mut c_char {
    if name.is_null() {
        return std::ptr::null_mut();
    }
    let name = unsafe { CStr::from_ptr(name) }.to_string_lossy().into_owned();

    let out = match resolve(&name) {
        Outcome::Ok(records) => {
            let mut s = String::from("ok");
            for r in records {
                s.push('\n');
                s.push_str(&r);
            }
            s
        }
        Outcome::Insecure(msg) => format!("insecure\n{msg}"),
        Outcome::Failed(msg) => format!("error\n{msg}"),
    };

    match CString::new(out) {
        Ok(c) => c.into_raw(),
        Err(_) => CString::new("error\ninternal").unwrap().into_raw(),
    }
}

/// Free a buffer returned by [`oa_secure_txt`].
#[no_mangle]
pub extern "C" fn oa_free(ptr: *mut c_char) {
    if !ptr.is_null() {
        unsafe {
            let _ = CString::from_raw(ptr);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn smoke() {
        // Live network. Prints the outcome for a few names. An unsigned domain
        // (google.com) should be reported "insecure" (fail closed); a name with
        // no records should be "ok" with zero records. In a sandbox that cannot
        // fetch the (large) DNSSEC records, expect "failed" (timeout) instead.
        for name in ["google.com", "_openalias-payment.donate.openalias.org"] {
            let word = match resolve(name) {
                Outcome::Ok(records) => format!("ok ({} records)", records.len()),
                Outcome::Insecure(msg) => format!("insecure ({msg})"),
                Outcome::Failed(msg) => format!("failed ({msg})"),
            };
            println!("resolve({name}) -> {word}");
        }
    }
}
