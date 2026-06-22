#!/usr/bin/env python3
"""Download Marker/Surya model weights into the runtime model directory."""
import os
from pathlib import Path

from modelscope import snapshot_download

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(os.environ.get("AUTOSLIDES_MARKER_MODEL_DIR", PROJECT_ROOT / ".runtime" / "models"))


def download_model() -> None:
    """Download the marker-pdf model"""
    print("Downloading marker-pdf model...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download("Lixiang/marker-pdf", local_dir=str(MODEL_DIR))
    print("Model download completed!")


if __name__ == "__main__":
    download_model()
