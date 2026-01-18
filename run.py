from openfilter.filter_runtime.filter import Filter
from openfilter.filter_runtime.filters.video_in import VideoIn
from openfilter.filter_runtime.filters.webvis import Webvis
from filter_yolo import YOLOFilter
# from filter_db import DBFilter
import os

#file://video/example_video.mp4!loop

if __name__ == "__main__":
    Filter.run_multi([
        (VideoIn, dict(
            sources=[{
                'source': 'webcam://0',
                'topic': 'main',
                'options': {}
            }],
            outputs='tcp://*:5550',
        )),
        (YOLOFilter, dict(
            sources='tcp://localhost:5550',
            outputs='tcp://*:5552',
        )),
        #(DBFilter, dict(
        #    sources='tcp://localhost:5552',
        #    outputs='tcp://*:5554',
        #)),
        (Webvis, dict(
            sources=['tcp://localhost:5552'],
        )),
    ])