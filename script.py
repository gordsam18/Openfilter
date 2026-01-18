from openfilter.filter_runtime import Frame, Filter
from openfilter.filter_runtime.filters.video_in import VideoIn

class MyFilter(Filter):
    def setup(self, config):  # not needed, just to show usage
        print(f'MyFilter setup: {config.my_happy_little_option=}')

    def process(self, frames):
        frame = frames['main'].rw_rgb  # take the most optimal path to a writable RGB format image from whatever came in
        image = frame.image
        data  = frame.data

        # TODO: process image and data here
        image[:, :, 1] = 0  # zero out the green channel

        return Frame(image, data, 'RGB')  # return frame with new image data, WARNING! if you don't pass the data through the FPS on output videos will be wrong! Specifically the 'meta' object in `.data`, but best practice is to copy the incoming data and add your own data to it.

    def shutdown(self):  # not needed, just to show usage
        print('MyFilter shutting down')

if __name__ == '__main__':
    Filter.run_multi([
        (VideoIn,  dict(sources='/Users/samgordon/Desktop/Projects/Openfilter/nature_video.mp4!sync', outputs='tcp://*')),  # the '!sync' option reads the video one frame at a time without skipping anything as fast as possible for processing

        (MyFilter, dict(sources='tcp://localhost',                    outputs='tcp://*:5552', my_happy_little_option='YAY')),

        (VideoIn,  dict(sources='tcp://localhost:5552',               outputs='file://output.mp4')),
    ])