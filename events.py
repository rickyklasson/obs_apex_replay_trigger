import easyocr
import numpy as np

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from PIL import Image

class EventType(Enum):
    NONE = 'none'
    ASSIST = 'assist'
    KNOCK = 'knock'
    SQUAD_WIPE = 'squad_wipe'
    GAME_START = 'game_start'
    GAME_END = 'game_end'
    VICTORY = 'victory'

    @classmethod
    def from_str(cls, trigger: str) -> 'EventType':
        return cls.__members__.get(trigger.upper(), cls.NONE)


@dataclass
class Event:
    type: EventType
    text: str

_ocr_reader = easyocr.Reader(['en'], gpu=True)


def from_file(image_file: Path) -> Image:
    return Image.open(image_file)


def detect_event(image: Image) -> Event | None:
    img_array = np.array(image)
    results = _ocr_reader.readtext(img_array)

    for _, text, __ in results:
        if 'ASSIST' in text:
            return Event(EventType.ASSIST, text)
        elif 'KNOCKED DOWN' in text or 'RE-KNOCKED' in text:
            return Event(EventType.KNOCK, text)
        elif 'SQUAD WIPE' in text:
            return Event(EventType.SQUAD_WIPE, text)
        elif 'YOUR SQUAD' in text:
            return Event(EventType.GAME_START, text)
        elif 'SUMMARY' in text:
            return Event(EventType.GAME_END, text)
        elif 'CHAMPION' in text:
            return Event(EventType.VICTORY, text)

    return Event(EventType.NONE, '')