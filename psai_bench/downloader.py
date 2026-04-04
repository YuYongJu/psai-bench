"""Dataset download utilities for PSAI-Bench.

Downloads UCF Crime test videos from HuggingFace. The full test set (290 videos)
requires downloading multiple large zip files (~28GB total). A 5-video sample
is available for pipeline testing (~114MB).

Usage:
    # Quick test (5 videos, ~114MB)
    psai-bench download-ucf --sample

    # Full test set (290 videos, ~28GB)
    psai-bench download-ucf --full
"""

import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download


# The UCF Crime test videos are spread across these zip files.
# Anomaly videos (140): split across 4 parts, each containing multiple categories.
# Normal videos (150): in a dedicated zip.
FULL_ZIPS = [
    ("Anomaly-Videos-Part-1.zip", 5.8),  # (filename, approx GB)
    ("Anomaly-Videos-Part-2.zip", 6.2),
    ("Anomaly-Videos-Part-3.zip", 5.2),
    ("Anomaly-Videos-Part-4.zip", 6.1),
    ("Testing_Normal_Videos.zip", 4.3),
]

SAMPLE_ZIP = ("test.zip", 0.11)  # 5-video sample

# The 290 test video filenames (from Anomaly_Test.txt)
# Used to filter extracted videos to only the test set
TEST_SPLIT_PATH = "UCF_Crimes-Train-Test-Split/Anomaly_Detection_splits/Anomaly_Test.txt"


def download_sample(output_dir: str = "data/raw/ucf_crime") -> list[str]:
    """Download the 5-video test sample (~114MB).

    Good for verifying the pipeline works before committing to the full download.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Downloading test sample ({SAMPLE_ZIP[1]:.0f} MB)...")
    zip_path = hf_hub_download(
        "jinmang2/ucf_crime", SAMPLE_ZIP[0], repo_type="dataset"
    )

    print(f"Extracting to {out}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out)

    videos = sorted(out.rglob("*.mp4"))
    print(f"Extracted {len(videos)} sample videos")
    return [str(v) for v in videos]


def download_full(output_dir: str = "data/raw/ucf_crime") -> list[str]:
    """Download all 290 UCF Crime test videos (~28GB).

    Downloads 5 zip files from HuggingFace, extracts them, then filters
    to only the 290 videos in the official test split.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # First, get the test split list so we know which videos to keep
    print("Downloading test split list...")
    split_path = hf_hub_download(
        "jinmang2/ucf_crime", TEST_SPLIT_PATH, repo_type="dataset"
    )
    with open(split_path) as f:
        test_filenames = {line.strip().split("/")[-1] for line in f if line.strip()}
    print(f"Test split contains {len(test_filenames)} videos")

    total_gb = sum(size for _, size in FULL_ZIPS)
    print(f"\nDownloading {len(FULL_ZIPS)} zip files (~{total_gb:.0f} GB total)...")
    print("This will take a while. Files are cached by HuggingFace after first download.\n")

    all_videos = []

    for zip_name, size_gb in FULL_ZIPS:
        print(f"  Downloading {zip_name} (~{size_gb:.1f} GB)...")
        zip_path = hf_hub_download(
            "jinmang2/ucf_crime", zip_name, repo_type="dataset"
        )

        print(f"  Extracting test videos from {zip_name}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                filename = Path(member).name
                if filename in test_filenames and filename.endswith(".mp4"):
                    zf.extract(member, out)
                    all_videos.append(str(out / member))

        print(f"  Done. Running total: {len(all_videos)} test videos extracted.")

    print(f"\nComplete. {len(all_videos)} test videos in {out}")

    missing = test_filenames - {Path(v).name for v in all_videos}
    if missing:
        print(f"WARNING: {len(missing)} test videos not found in zip files:")
        for m in sorted(missing)[:10]:
            print(f"  {m}")

    return all_videos
