"""Maps real UCF Crime test videos to PSAI-Bench Visual Track scenarios.

This module bridges the gap between our synthetic metadata and real video files.
For each test video, it:
1. Parses the official temporal annotations (anomaly start/end frames)
2. Maps to the correct UCF Crime category
3. Generates a PSAI-Bench alert with visual_data.uri pointing to the real video
4. Ensures the scenario metadata is consistent with what the video actually shows

The 290 UCF Crime test videos (140 anomaly + 150 normal) produce 290 Visual Track
scenarios. Each scenario has BOTH real video AND synthetic contextual metadata.
"""

import json
from pathlib import Path

import numpy as np

from psai_bench.distributions import (
    EXPECTED_ACTIVITIES,
    TOD_OPTIONS,
    TOD_WEIGHTS_BENIGN,
    TOD_WEIGHTS_THREAT,
    UCF_CATEGORY_MAP,
    sample_device,
    sample_site_type,
    sample_weather,
    sample_zone,
)
from psai_bench.generators import (
    SITE_CATEGORY_BLOCKLIST,
    _assign_difficulty,
    _generate_recent_events,
    _generate_timestamp,
)


def parse_temporal_annotations(annotation_path: str) -> dict:
    """Parse UCF Crime temporal annotation file.

    Format: filename  category  start1  end1  start2  end2
    Where -1 -1 means no second anomaly segment.

    Returns:
        Dict mapping filename to {category, segments: [(start, end), ...]}
    """
    annotations = {}
    with open(annotation_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            filename = parts[0]
            category = parts[1]
            s1, e1 = int(parts[2]), int(parts[3])
            s2, e2 = int(parts[4]), int(parts[5])

            segments = []
            if s1 >= 0 and e1 >= 0:
                segments.append((s1, e1))
            if s2 >= 0 and e2 >= 0:
                segments.append((s2, e2))

            annotations[filename] = {
                "category": category,
                "segments": segments,
            }
    return annotations


def parse_test_split(test_split_path: str) -> list[dict]:
    """Parse the Anomaly_Test.txt file listing test videos.

    Returns:
        List of dicts with path, filename, category, is_normal.
    """
    videos = []
    with open(test_split_path) as f:
        for line in f:
            path = line.strip()
            if not path:
                continue
            parts = path.split("/")
            category = parts[0]
            filename = parts[-1]
            is_normal = "Normal" in category
            videos.append({
                "path": path,
                "filename": filename,
                "category": "Normal" if is_normal else category,
                "is_normal": is_normal,
            })
    return videos


class VisualTrackMapper:
    """Generate Visual Track scenarios mapped to real UCF Crime test videos."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.seed = seed

    def generate_from_annotations(
        self,
        test_videos: list[dict],
        annotations: dict,
        video_dir: str | None = None,
        variants_per_video: int = 1,
    ) -> list[dict]:
        """Generate Visual Track scenarios from real UCF Crime test videos.

        Args:
            test_videos: Parsed test split (from parse_test_split)
            annotations: Parsed temporal annotations (from parse_temporal_annotations)
            video_dir: Local directory containing downloaded videos.
                       If None, URIs reference the HuggingFace dataset path.
            variants_per_video: Number of contextual variants per video. Each variant
                uses the same video but different operational context (zone, site type,
                time of day, weather). This is legitimate augmentation: the same
                burglary video at a solar farm at night IS a different triage scenario
                than at a commercial building during the day.

        Returns:
            List of PSAI-Bench alert dicts with visual_data pointing to real videos.
        """
        scenarios = []
        scenario_idx = 0

        for video in test_videos:
          for variant in range(variants_per_video):
            cat = video["category"]
            filename = video["filename"]

            # Get mapping config
            if cat in UCF_CATEGORY_MAP:
                mapping = UCF_CATEGORY_MAP[cat]
            else:
                # Unknown category, treat as Normal
                mapping = UCF_CATEGORY_MAP["Normal"]

            gt = mapping["ground_truth"]
            tod_weights = TOD_WEIGHTS_THREAT if gt == "THREAT" else TOD_WEIGHTS_BENIGN
            time_of_day = self.rng.choice(TOD_OPTIONS, p=tod_weights)

            zone = sample_zone(self.rng)
            device = sample_device(zone["type"], self.rng)
            weather = sample_weather(time_of_day, self.rng)

            # Sample site type, rejecting implausible combos
            site_type = sample_site_type(self.rng)
            for _ in range(10):
                blocked = SITE_CATEGORY_BLOCKLIST.get(site_type, set())
                if cat not in blocked:
                    break
                site_type = sample_site_type(self.rng)

            severity = self.rng.choice(mapping["severity_range"])
            description = self.rng.choice(mapping["description_templates"])

            difficulty = _assign_difficulty(
                cat, zone["sensitivity"], time_of_day, device["false_positive_rate"],
                self.rng, dataset="ucf_crime",
            )

            # Build video reference
            annotation = annotations.get(filename, {})
            segments = annotation.get("segments", [])

            if video_dir:
                uri = str(Path(video_dir) / video["path"])
            else:
                # Reference to HuggingFace dataset path
                uri = f"hf://jinmang2/ucf_crime/{video['path']}"

            # Estimate duration from annotation segments (rough: last frame / 30fps)
            if segments:
                max_frame = max(e for _, e in segments)
                estimated_duration = max_frame / 30.0  # approximate at 30fps
            else:
                estimated_duration = 60.0  # default for normal videos

            alert = {
                "alert_id": f"ucf-visual-{scenario_idx:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "visual",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone["type"], time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": [],
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": {
                    "type": "video_clip",
                    "uri": uri,
                    "duration_sec": round(estimated_duration, 1),
                    "resolution": "320x240",  # UCF Crime standard resolution
                },
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": gt,
                    "difficulty": difficulty,
                    "source_dataset": "ucf_crime",
                    "source_category": cat,
                    "source_filename": filename,
                    "anomaly_segments": segments,
                    "seed": self.seed,
                    "index": scenario_idx,
                    "variant": variant,
                },
            }
            scenarios.append(alert)
            scenario_idx += 1

        return scenarios


def download_test_videos(
    output_dir: str = "data/raw/ucf_crime",
    max_videos: int | None = None,
) -> list[str]:
    """Download UCF Crime test videos from HuggingFace.

    Downloads from the zip files containing anomaly and normal test videos.
    This is a large download (~5GB for test set). Progress is shown.

    Args:
        output_dir: Where to save videos
        max_videos: Limit downloads for testing (None = all 290)

    Returns:
        List of downloaded file paths
    """
    from huggingface_hub import hf_hub_download

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Download the test zip (contains all 290 test videos, ~118MB)
    print("Downloading UCF Crime test annotations...")
    test_zip_path = hf_hub_download(
        "jinmang2/ucf_crime",
        "test.zip",
        repo_type="dataset",
    )
    print(f"Downloaded test.zip to cache: {test_zip_path}")

    # Extract
    import zipfile
    print(f"Extracting to {out}...")
    with zipfile.ZipFile(test_zip_path, "r") as zf:
        members = zf.namelist()
        mp4_files = [m for m in members if m.endswith(".mp4")]
        print(f"Found {len(mp4_files)} video files in archive")

        if max_videos:
            mp4_files = mp4_files[:max_videos]

        for f in mp4_files:
            zf.extract(f, out)

    extracted = list(out.rglob("*.mp4"))
    print(f"Extracted {len(extracted)} videos to {out}")
    return [str(p) for p in extracted]
