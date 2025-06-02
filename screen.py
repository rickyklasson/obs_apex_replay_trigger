from PIL import Image

import mss

CROP_BBOX = (600, 760, 1320, 795)  # Bbox for event texts when Apex is running at 1920x1080.

_screen_capture = mss.mss()

def grab_screen_event_region() -> Image:
    region = {
        'left': CROP_BBOX[0],
        'top': CROP_BBOX[1],
        'width': CROP_BBOX[2] - CROP_BBOX[0],
        'height': CROP_BBOX[3] - CROP_BBOX[1]
    }
    screenshot = _screen_capture.grab(region)
    return Image.frombytes('RGB', screenshot.size, screenshot.rgb)