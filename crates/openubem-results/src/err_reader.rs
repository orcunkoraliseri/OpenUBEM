//! Whitespace-tolerant matcher for EnergyPlus `.err` file markers (`OPEN-45`, `err_parse.py`).

/// Inspect one stripped line for a `** Severe **` marker.
#[inline]
pub fn is_severe_line(line: &str) -> bool {
    has_star_tag(line, "Severe")
}

/// Inspect one stripped line for a `** Fatal **` marker.
#[inline]
pub fn is_fatal_line(line: &str) -> bool {
    has_star_tag(line, "Fatal")
}

/// Inspect one stripped line for a `** Warning **` marker.
#[inline]
pub fn is_warning_line(line: &str) -> bool {
    has_star_tag(line, "Warning")
}

#[inline]
fn has_star_tag(line: &str, keyword: &str) -> bool {
    let s = line.trim_start();
    let Some(after_open) = s.strip_prefix("**") else {
        return false;
    };
    let ws1 = after_open.len() - after_open.trim_start().len();
    if ws1 == 0 {
        return false;
    }
    let after_ws1 = &after_open[ws1..];
    let Some(after_kw) = after_ws1.strip_prefix(keyword) else {
        return false;
    };
    let ws2 = after_kw.len() - after_kw.trim_start().len();
    if ws2 == 0 {
        return false;
    }
    after_kw[ws2..].starts_with("**")
}

/// Return every trimmed line carrying a `** Severe **` marker.
pub fn iter_severe(text: &str) -> Vec<&str> {
    text.lines()
        .filter(|line| is_severe_line(line))
        .map(str::trim)
        .collect()
}

/// Return the first `** Severe **` line trimmed, or empty string if none.
pub fn first_severe(text: &str) -> &str {
    text.lines()
        .find(|line| is_severe_line(line))
        .map(str::trim)
        .unwrap_or("")
}

/// Count lines carrying a `** Severe **` marker.
pub fn count_severe(text: &str) -> usize {
    text.lines().filter(|line| is_severe_line(line)).count()
}

/// True iff `text` carries at least one `** Fatal **` marker line.
pub fn has_fatal(text: &str) -> bool {
    text.lines().any(is_fatal_line)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn matches_single_and_double_spaces_open45() {
        let sample = "   **  Severe  **  Zone problem\n** Warning ** minor\n **  Fatal  **  Stopped\n";
        assert_eq!(count_severe(sample), 1);
        assert_eq!(first_severe(sample), "**  Severe  **  Zone problem");
        assert!(has_fatal(sample));
        assert!(is_warning_line("** Warning ** minor"));
        assert!(!is_severe_line("**Severe** tight"));
    }
}
