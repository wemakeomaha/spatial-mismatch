from __future__ import annotations

import os
import shutil
from pathlib import Path

import pandas as pd

from _common import DATA_RAW, ensure_dirs, download, lodes_url, tigerweb_tract_url, write_json


def import_inventory() -> dict:
    source = Path(os.getenv("INVENTORY_XLSX", r"C:\Users\moatejioye\Downloads\Job_Housing Mismatch.xlsx"))
    target = DATA_RAW / "Job_Housing_Mismatch_inventory.xlsx"
    if not source.exists():
        return {"ok": False, "source": str(source), "error": "Workbook not found. Set INVENTORY_XLSX."}
    shutil.copy2(source, target)
    df = pd.read_excel(source).fillna("")
    csv_target = DATA_RAW / "dataset_inventory.csv"
    df.to_csv(csv_target, index=False)
    return {"ok": True, "source": str(source), "xlsx": str(target), "csv": str(csv_target), "rows": len(df)}


def download_tracts() -> dict:
    target = DATA_RAW / "douglas_county_tracts_tigerweb.geojson"
    attempts = []
    for layer_id in [0, 4, 7, 10]:
        result = download(tigerweb_tract_url(layer_id), target)
        attempts.append(result)
        if result["ok"] and target.exists() and target.stat().st_size > 500:
            return {**result, "layer_id": layer_id, "attempts": list(attempts)}
    return {"ok": False, "path": str(target), "attempts": attempts}


def main() -> None:
    ensure_dirs()
    manifest = {
        "inventory": import_inventory(),
        "tract_boundaries": download_tracts(),
        "lodes_wac": download(lodes_url("wac"), DATA_RAW / "ne_wac_S000_JT00.csv.gz"),
        "lodes_rac": download(lodes_url("rac"), DATA_RAW / "ne_rac_S000_JT00.csv.gz"),
        "lodes_od": download(lodes_url("od"), DATA_RAW / "ne_od_main_JT00.csv.gz"),
        "gtfs": None,
    }

    gtfs_url = os.getenv("GTFS_URL", "").strip()
    if gtfs_url:
        manifest["gtfs"] = download(gtfs_url, DATA_RAW / "omaha_gtfs.zip")
    else:
        placeholder = DATA_RAW / "GTFS_PLACEHOLDER.md"
        placeholder.write_text(
            "# GTFS placeholder\n\n"
            "Set `GTFS_URL` to a Metro Transit/Omaha static GTFS zip URL and rerun "
            "`scripts/01_download_or_import_data.py` to calculate transit access. "
            "Until then, transit access is left missing in the tract metrics.\n",
            encoding="utf-8",
        )
        manifest["gtfs"] = {"ok": False, "path": str(placeholder), "needed": "Static GTFS zip URL"}

    write_json(DATA_RAW / "download_manifest.json", manifest)
    print(f"Wrote {DATA_RAW / 'download_manifest.json'}")


if __name__ == "__main__":
    main()
