"""
Download HAM10000 dataset from Harvard Dataverse (public, no credentials needed).

DOI: https://doi.org/10.7910/DVN/DBW86T

Usage:
    python ml/scripts/download_ham10000.py

Output structure under ml/data/ham1000/:
    HAM10000_metadata
    HAM10000_images_part_1/   (or images flat in ham1000/ — both work)
    HAM10000_images_part_2/
    HAM10000_segmentations_lesion_tschandl/
"""

import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

DATAVERSE_API = "https://dataverse.harvard.edu/api"
PERSISTENT_ID = "doi:10.7910/DVN/DBW86T"

ML_DIR  = Path(__file__).resolve().parents[1]
HAM_DIR = ML_DIR / "data" / "ham1000"

WANTED = {
    "HAM10000_images_part_1.zip",
    "HAM10000_images_part_2.zip",
    "HAM10000_segmentations_lesion_tschandl.zip",
    "HAM10000_metadata.tab",
}


def _seg_dir() -> Path:
    """Return segmentation masks folder regardless of nested/flat structure."""
    nested = HAM_DIR / "HAM10000_segmentations_lesion_tschandl" / "HAM10000_segmentations_lesion_tschandl"
    flat   = HAM_DIR / "HAM10000_segmentations_lesion_tschandl"
    return nested if nested.exists() else flat


def _already_complete() -> bool:
    seg = _seg_dir()
    return (
        (HAM_DIR / "HAM10000_metadata").exists()
        and seg.exists()
        and any(seg.glob("*.png"))
        and any(HAM_DIR.rglob("ISIC_*.jpg"))
    )


def _get_file_list() -> list[dict]:
    url = f"{DATAVERSE_API}/datasets/:persistentId/?persistentId={PERSISTENT_ID}"
    print("Querying Dataverse API...")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()["data"]["latestVersion"]["files"]


def _download_file(file_id: int, filename: str, dest: Path) -> None:
    url = f"{DATAVERSE_API}/access/datafile/{file_id}"
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(
            desc=filename,
            total=total,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))


def _extract(zip_path: Path) -> None:
    print(f"Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(HAM_DIR)
    zip_path.unlink()


def main() -> None:
    if _already_complete():
        print("HAM10000 dataset already complete. Nothing to do.")
        return

    HAM_DIR.mkdir(parents=True, exist_ok=True)

    files = _get_file_list()
    to_download = [f for f in files if f["dataFile"]["filename"] in WANTED]

    if not to_download:
        raise RuntimeError(
            "Expected files not found on Dataverse. Download manually from:\n"
            "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T"
        )

    total_gb = sum(f["dataFile"].get("filesize", 0) for f in to_download) / 1e9
    print(f"\nFiles to download: {len(to_download)}  (~{total_gb:.1f} GB)\n")

    for entry in to_download:
        df       = entry["dataFile"]
        file_id  = df["id"]
        filename = df["filename"]
        dest     = HAM_DIR / filename

        if dest.exists():
            print(f"  {filename} already exists, skipping.")
        else:
            _download_file(file_id, filename, dest)

        if filename.endswith(".zip"):
            _extract(dest)
        elif filename == "HAM10000_metadata.tab":
            # Rename to match the name expected by the pipeline scripts
            dest.rename(HAM_DIR / "HAM10000_metadata")
            print(f"  Saved as HAM10000_metadata")

    if _already_complete():
        print("\nDataset ready at:", HAM_DIR)
    else:
        print("\nWARNING: final structure is incomplete. Check:", HAM_DIR)


if __name__ == "__main__":
    main()
