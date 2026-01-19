from openfilter.filter_runtime.filter import Filter, FilterConfig, Frame
import logging
import cv2
import numpy as np
import csv
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVFilterConfig(FilterConfig):
    debug: bool = False

def ensure_csv(path: str):
    """Ensure the CSV file exists and has a header."""
    csv_path = Path(path)
    if not csv_path.exists():
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ts", "change_type", "previous_count", "current_count", "notes"])
    return str(csv_path)

def write_person_count_csv(path: str, current_count: int, previous_count: int, notes: str = ""):
    """Append a person-count change row to CSV, ensuring the CSV exists first."""
    csv_path = ensure_csv(path)
    try:
        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.utcnow().isoformat(),
                                ("increase" if current_count > previous_count else "decrease"),
                                previous_count,
                                current_count,
                                notes])
    except Exception as e:
        logger.error(f"Failed to write person count to CSV {csv_path}: {e}")

def add_text_to_image(image, text, position=(10, 30), font_scale=1.0, color=(0, 255, 0), thickness=2):
    """Add text to a numpy array image"""
    cv2.putText(
        image,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        thickness
    )
    return image

class CSVFilter(Filter):
    @classmethod
    # def normalize_config(self, config: CSVFilterConfig):
    #     config = CSVFilterConfig(super().normalize_config(config))
    #     return config

    def setup(self, config: CSVFilterConfig):
        #logger.info(f"CSVFilter setup with config: {config}")
        self.last_person_count = 0
        load_dotenv()
        # CSV path can be set via LOG_CSV env var; default to person_counts.csv
        self.csv_path = os.getenv("LOG_CSV", "person_counts.csv")
        # ensure CSV exists
        self.csv_path = ensure_csv(self.csv_path)

    def log_person_count_change(self, current_count, previous_count, frame_data, objects):
        """Record person count changes into CSV using `write_person_count_csv`."""
        if current_count == previous_count:
            return

        change_type = "increase" if current_count > previous_count else "decrease"
        notes = f"Person count {change_type}d from {previous_count} to {current_count}"
        write_person_count_csv(self.csv_path, current_count, previous_count, notes)
        logger.info(f"Logged person count {change_type}: {previous_count} -> {current_count} (csv:{self.csv_path})")

    def process(self, frames: dict[str, Frame]):
        # self.last_person_count = 0
        frame = frames.get("main")
        image = frame.rw_rgb.image
        objects = frame.data.get("objects", [])

        class_counts = {}

        for obj in objects:
            class_name = obj.get("class")
            confidence = obj.get("confidence", 0)

            # optional confidence filter
            if class_name == "person" and confidence < 0.7:
                continue

            class_counts[class_name] = class_counts.get(class_name, 0) + 1

            # draw bounding box if present
            if class_name == "person" and "bbox" in obj:
                x1, y1, x2, y2 = obj["bbox"]
                cv2.rectangle(
                    image,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    (0, 255, 0),
                    2
                )

        current_person_count = class_counts.get("person", 0)

        if current_person_count != self.last_person_count:
            self.log_person_count_change(
                current_person_count,
                self.last_person_count,
                frame.data,
                objects
            )
            self.last_person_count = current_person_count

        # build overlay text
        text = f"People: {current_person_count}"
        for cls, count in class_counts.items():
            if cls != "person":
                text += f" | {cls}: {count}"

        cv2.putText(
            image,
            text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        frames["main"] = Frame(
            image,
            {**frame.data},
            format="RGB"
        )

        return frames


if __name__ == "__main__":
    CSVFilter.run()
