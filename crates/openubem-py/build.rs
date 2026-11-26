//! Build script for `openubem-py`.
//!
//! When running `cargo test` on macOS (without the `extension-module` feature),
//! embeds the active Python's `lib_dir` as an rpath so `@rpath/libpython*.dylib`
//! (e.g., Conda/uv standalone Python builds) resolves without requiring
//! `DYLD_LIBRARY_PATH`. Production extension wheels built by `maturin` enable
//! `extension-module` and omit this rpath completely.

fn main() {
    pyo3_build_config::use_pyo3_cfgs();
    #[cfg(all(target_os = "macos", not(feature = "extension-module")))]
    {
        let cfg = pyo3_build_config::get();
        if let Some(lib_dir) = cfg.lib_dir() {
            println!("cargo:rustc-link-arg=-Wl,-rpath,{lib_dir}");
        }
    }
}
