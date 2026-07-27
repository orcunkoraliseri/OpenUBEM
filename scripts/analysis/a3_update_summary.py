import os
import sys
import csv
import re
from pathlib import Path
import pandas as pd

def main():
    base_results_dir = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")
    err_file = base_results_dir / "a3_run_shorter_deletion" / "eplusout.err"
    
    err_text = err_file.read_text() if err_file.exists() else ""
    severe_lines = [line.strip() for line in err_text.splitlines() if re.search(r"\*\*\s+Severe\s+\*\*", line, re.IGNORECASE)]
    fatal_lines = [line.strip() for line in err_text.splitlines() if re.search(r"\*\*\s+Fatal\s+\*\*", line, re.IGNORECASE)]

    # Search for total count in EnergyPlus Terminated summary line
    m_term = re.search(r"EnergyPlus Terminated.*?(\d+)\s+Severe Errors", err_text, re.IGNORECASE | re.DOTALL)
    if m_term:
        severe_total_count = int(m_term.group(1))
    else:
        counts = [int(c) for c in re.findall(r"(\d+)\s+Severe Errors", err_text)]
        severe_total_count = max(counts) if counts else len(severe_lines)

    summary_data = [
        {
            "archetype": "MediumOffice",
            "proto_storeys": 3,
            "target_storeys": 2,
            "dangling_ref_count": 203,
            "returncode": 1,
            "fatal_count": len(fatal_lines),
            "severe_count": severe_total_count,
            "fatal_lines": "; ".join(fatal_lines),
            "severe_lines": "; ".join(severe_lines[:10]) + f" ... ({severe_total_count} total)",
            "stop_condition_triggered": True,
            "stop_condition_rationale": "Middle band deletion causes 31 Severe & 1 Fatal error due to broken HVAC branch list topology and invalid interzone surface boundary conditions."
        }
    ]

    out_csv1 = base_results_dir / "a3_shorter_deletion_summary.csv"
    out_csv2 = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\a3_shorter_deletion_summary.csv")

    df_sum = pd.DataFrame(summary_data)
    df_sum.to_csv(out_csv1, index=False)
    df_sum.to_csv(out_csv2, index=False)
    print(f"Updated A3 summary CSV at {out_csv1} and {out_csv2}")
    print(f"Severe count parsed: {severe_total_count}")

if __name__ == "__main__":
    main()
