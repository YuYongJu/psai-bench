"""Frame extraction baseline for PSAI-Bench visual track.

Requires psai-bench[visual]: pip install "psai-bench[visual]"

DESIGN CONSTRAINT (FRAME-02): extract_keyframes() MUST NOT use anomaly_segments
for frame selection. Selection is purely uniform-interval (every N seconds).
This is the fairness constraint for the frame extraction baseline — the model
sees the same frames regardless of whether anomaly_segments exist.
"""


def extract_keyframes(
    video_path: str,
    keyframe_interval_sec: float = 5.0,
    max_frames: int = 50,
) -> list[bytes]:
    """Extract JPEG frames at uniform intervals from a video file.

    Args:
        video_path: Path to video file (local path or URL readable by cv2).
        keyframe_interval_sec: Seconds between sampled frames. Default 5.0.
        max_frames: Hard cap on returned frames (prevents memory issues on long videos).

    Returns:
        List of JPEG-encoded bytes (not base64 — callers encode if needed).

    Raises:
        ImportError: If opencv-python-headless is not installed.
        FileNotFoundError: If video_path does not exist or cannot be opened.
        ValueError: If keyframe_interval_sec <= 0.
    """
    if keyframe_interval_sec <= 0:
        raise ValueError(f"keyframe_interval_sec must be > 0, got {keyframe_interval_sec}")

    try:
        import cv2
    except ImportError as exc:
        raise ImportError(
            "opencv-python-headless is required for frame extraction. "
            'Install with: pip install "psai-bench[visual]"'
        ) from exc

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    interval_frames = max(1, int(fps * keyframe_interval_sec))

    frames: list[bytes] = []
    frame_idx = 0

    try:
        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % interval_frames == 0:
                ok, buf = cv2.imencode(".jpg", frame)
                if ok:
                    frames.append(bytes(buf))
            frame_idx += 1
    finally:
        cap.release()

    return frames
