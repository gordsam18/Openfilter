from openfilter.filter_runtime.filter import Filter, FilterConfig, Frame
from detect_objects import detect_objects_from_array
import logging
from pathlib import Path
import csv
from datetime import datetime
import cv2



logger = logging.getLogger(__name__)

class YOLOFilterConfig(FilterConfig):
    debug: bool = False

class YOLOFilter(Filter):
    @classmethod
    def normalize_config(self, config: YOLOFilterConfig):
        config = YOLOFilterConfig(super().normalize_config(config))
        return config

    def setup(self, config: YOLOFilterConfig):
        logger.info(f"YOLOFilter setup with config: {config}")
        self.last_person_count = 0

        log_dir = Path("/tmp/openfilter")
        log_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = log_dir / "person_count_log.csv"


    def write_person_count_csv(self, path: str, current_count: int, previous_count: int, notes: str = ""):
        """Append a person-count change row to CSV, ensuring the CSV exists first."""
        csv_path = Path(path)
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

    def log_person_count_change(self, current_count, previous_count, frame_data, objects):
        """Record person count changes into CSV using `write_person_count_csv`."""
        if current_count == previous_count:
            return

        change_type = "increase" if current_count > previous_count else "decrease"
        notes = f"Person count {change_type}d from {previous_count} to {current_count}"

        self.write_person_count_csv(self.csv_path, current_count, previous_count, notes)

        logger.info(f"Logged person count {change_type}: {previous_count} -> {current_count} (csv:{self.csv_path})")

    def process(self, frames: dict[str, Frame]):
        frame = frames.get("main")
        image = frame.rw_rgb.image

        # Detector
        detected_objects = detect_objects_from_array(image)

        person_count = 0

        # Draw boxes
        for obj in detected_objects:
            class_name = obj.get("class")
            confidence = obj.get("confidence", 0)

            if class_name != "person" or confidence < 0.7:
                continue

            person_count += 1

            # Box around person
            # x1, y1, x2, y2 = map(int, obj["bbox"])

            # cv2.rectangle(
            #     image,
            #     (x1, y1),
            #     (x2, y2),
            #     (0, 255, 0),  # green
            #     2
            # )

        # Log count change
        if person_count != self.last_person_count:
            logger.info(
                f"Person count changed: {self.last_person_count} → {person_count}"
            )
            self.last_person_count = person_count

        # Text overlay (top-left)
        cv2.putText(
            image,
            f"People detected: {person_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        # Return modified frame
        frames["main"] = Frame(
            image,
            frame.data,
            format="RGB"
        )

        return frames


if __name__ == "__main__":
    YOLOFilter.run()