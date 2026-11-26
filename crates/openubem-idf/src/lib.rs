//! `openubem-idf` — pure-Rust EnergyPlus IDF/ExpIDF parser, Schedule compiler, modal CTF, & ScriptF.

pub mod ctf;
pub mod error;
pub mod parser;
pub mod schedules;
pub mod viewfactors;

pub use ctf::{LayerSpec, ModalConductionModel, build_modal_conduction};
pub use error::IdfError;
pub use parser::{
    RawIdfObject, check_surface_construction_links, determine_azimuth_and_tilt,
    newell_area_and_normal, parse_idf_bytes,
};
pub use schedules::{
    compile_schedule_compact_hourly, load_schedule_file_hourly, load_schedule_file_hourly_bytes,
    load_schedule_files_batch,
};
pub use viewfactors::{
    calc_approximate_view_factors, calc_script_f, calc_zone_view_and_script_f_batch,
    fix_view_factors,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_idf_bytes_handles_comments_and_semicolons() {
        let idf = b"! comment; comma, ignored\nZone,\n  Zone1, ! inline; comment\n  0.0,\n  10.0;\n";
        let objs = parse_idf_bytes(idf);
        assert_eq!(objs.len(), 1);
        assert_eq!(objs[0].obj_type, "ZONE");
        assert_eq!(objs[0].fields, vec!["Zone1", "0.0", "10.0"]);
    }

    #[test]
    fn schedule_file_fast_bytes_extracts_column() {
        let csv = b"Header\n1, 10.5, 99\n2, 20.25, 88\n3, 30.0, 77\n";
        let vals = load_schedule_file_hourly_bytes(csv, 2, 1, 3, b',').expect("valid csv");
        assert_eq!(vals, vec![10.5, 20.25, 30.0]);
    }

    #[test]
    fn modal_conduction_heavy_wall_conserves_heat() {
        let layers = vec![
            LayerSpec {
                name: "xps".into(),
                is_nomass: false,
                r_value: 0.0,
                thickness: 0.10,
                conductivity: 0.034,
                density: 35.0,
                specific_heat: 1400.0,
            },
            LayerSpec {
                name: "conc".into(),
                is_nomass: false,
                r_value: 0.0,
                thickness: 0.25,
                conductivity: 1.4,
                density: 2300.0,
                specific_heat: 1000.0,
            },
        ];
        let m = build_modal_conduction(&layers, 300.0, "THICK_WALL", 12).expect("valid ctf");
        assert!(m.num_modes > 0 && m.num_modes <= 12);
        assert!(m.u_steady > 0.3 && m.u_steady < 0.35);
    }

    #[test]
    fn viewfactors_and_script_f_row_sums_unity() {
        let areas = [45.0, 45.0, 18.0, 18.0, 14.0, 14.0];
        let az = [0.0, 0.0, 0.0, 180.0, 90.0, 270.0];
        let tilt = [180.0, 0.0, 90.0, 90.0, 90.0, 90.0];
        let cls = [1, 2, 0, 0, 0, 0];
        let emiss = [0.9; 6];
        let f = calc_approximate_view_factors(&areas, &az, &tilt, &cls);
        let ff = fix_view_factors(&areas, &f);
        let sf = calc_script_f(&areas, &ff, &emiss).expect("script f");
        for i in 0..6 {
            let row_sum: f64 = ff[i * 6..(i + 1) * 6].iter().sum();
            assert!((row_sum - 1.0).abs() < 1e-3, "row {i} vf sum={row_sum}");
            let sf_sum: f64 = sf[i * 6..(i + 1) * 6].iter().sum();
            assert!((sf_sum - emiss[i]).abs() < 1e-3, "row {i} sf sum={sf_sum}");
        }
    }
}
