from PIL import Image

import mss

_screen_capture = mss.mss()


def grab_region(region: str) -> Image:
    # These bboxes are valid when apex is running at 1920x1080.
    BBOXES = {
        'player_event': (600, 760, 1320, 795),  # Bbox for player event texts: 'KNOCKED', 'ASSIST' etc...
        'game_start': (760, 40, 1160, 110),  # BBox for game start text: 'YOUR SQUAD'
        'game_end': (980, 30, 1140, 60),  # Bbox for game end: 'SUMMARY'
        'victory': (820, 960, 1100, 1000),  # Bbox for victory: 'CHAMPION'
    }
    assert region in BBOXES

    bbox = BBOXES[region]
    region = {
        'left': bbox[0],
        'top': bbox[1],
        'width': bbox[2] - bbox[0],
        'height': bbox[3] - bbox[1]
    }
    screenshot = _screen_capture.grab(region)
    return Image.frombytes('RGB', screenshot.size, screenshot.rgb)