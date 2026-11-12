"""Image and video handler for HIMSETU ingestion pipeline.

Extracts image dimensions, mode, and format using Pillow.
For MP4 video files, extracts frame count and duration only.
Images are classified as IMAGERY; no automatic ice-label extraction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def extract(path: Path) -> Dict[str, Any]:
    """Extract metadata from an image or video file.

    For images (.png, .jpg, .jpeg): extracts width, height, colour mode,
    and format using Pillow.

    For video (.mp4): extracts frame count and duration using
    imageio if available, otherwise records minimal metadata.

    Args:
        path: Path to the image or video file.

    Returns:
        Dictionary with metadata keys and notes.

    Raises:
        ImportError: If Pillow is not installed for image files.
        ValueError: If the file cannot be opened.
    """
    ext = path.suffix.lower()

    if ext == ".mp4":
        return _extract_video(path)
    else:
        return _extract_image(path)


def _extract_image(path: Path) -> Dict[str, Any]:
    """Extract metadata from a PNG or JPEG image using Pillow."""
    try:
        from PIL import Image  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Pillow is required for image support. "
            "Install with: pip install pillow"
        ) from exc

    try:
        with Image.open(path) as img:
            width, height = img.size
            mode = img.mode
            fmt = img.format or path.suffix.upper().lstrip(".")
            return {
                "width_px": width,
                "height_px": height,
                "mode": mode,
                "format": fmt,
                "notes": [
                    "Image classified as IMAGERY. "
                    "No automatic scientific data extraction performed."
                ],
            }
    except Exception as exc:
        raise ValueError(
            f"Failed to open image file '{path}': {exc}"
        ) from exc


def _extract_video(path: Path) -> Dict[str, Any]:
    """Extract minimal metadata from an MP4 video file."""
    notes = [
        "Video classified as IMAGERY. "
        "Frame extraction for scientific use requires explicit analysis."
    ]

    # Attempt to use imageio for frame/duration info (optional)
    try:
        import imageio  # type: ignore

        reader = imageio.get_reader(str(path))
        meta = reader.get_meta_data()
        frame_count = meta.get("nframes", None)
        duration = meta.get("duration", None)
        fps = meta.get("fps", None)
        reader.close()

        return {
            "frame_count": frame_count,
            "duration_s": duration,
            "fps": fps,
            "notes": notes,
        }
    except ImportError:
        notes.append(
            "Install 'imageio[ffmpeg]' for video frame metadata extraction."
        )
    except Exception as exc:
        notes.append(f"Could not extract video metadata: {exc}")

    return {
        "frame_count": None,
        "duration_s": None,
        "fps": None,
        "notes": notes,
    }
