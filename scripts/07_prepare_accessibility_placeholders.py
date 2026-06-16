from __future__ import annotations

import pandas as pd

from _common import OUTPUT_CSV, OUTPUTS, ensure_dirs


def main() -> None:
    ensure_dirs()
    placeholder = pd.DataFrame(
        columns=[
            "GEOID",
            "jobs_reachable_30min_car",
            "jobs_reachable_30min_transit",
            "accessibility_status",
            "needed_inputs",
        ]
    )
    placeholder.to_csv(OUTPUT_CSV / "accessibility_30min_placeholder.csv", index=False)
    (OUTPUTS / "accessibility_placeholders.md").write_text(
        "# Future Accessibility Metrics\n\n"
        "This project is structured to add jobs reachable within 30 minutes by car and transit, "
        "but Phase 1 does not fake network accessibility.\n\n"
        "## Needed For Car Accessibility\n\n"
        "- Routable street network or travel-time API.\n"
        "- Tract origin points, preferably population-weighted centroids.\n"
        "- Job destination points or tract-level job allocation method.\n"
        "- Departure time assumptions and congestion treatment.\n\n"
        "## Needed For Transit Accessibility\n\n"
        "- Static GTFS feed with stops, routes, trips, stop_times, calendar, and calendar_dates.\n"
        "- Walking access assumptions to stops.\n"
        "- Transfer assumptions and maximum walking distance.\n"
        "- Departure time window, such as weekday 7:00-9:00 AM.\n"
        "- Routing engine such as OpenTripPlanner, r5py/R5, Conveyal, or a comparable API.\n\n"
        "## Planned Output Fields\n\n"
        "- `jobs_reachable_30min_car`\n"
        "- `jobs_reachable_30min_transit`\n"
        "- `share_county_jobs_reachable_30min_car`\n"
        "- `share_county_jobs_reachable_30min_transit`\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_CSV / 'accessibility_30min_placeholder.csv'}")


if __name__ == "__main__":
    main()
