from openfilter.filter_runtime.filter import Filter, FilterConfig, Frame
from detect_objects import detect_objects_from_array
import logging

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

    def process(self, frames: dict[str, Frame]):
        frame = frames.get('main')
        image = frame.rw_rgb.image # Get the image from the frame
        detected_objects = detect_objects_from_array(image)
        # logger.info(f"detected objects: {detected_objects}")
        frame.data['objects'] = detected_objects
        return frames

if __name__ == "__main__":
    YOLOFilter.run()