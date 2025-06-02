import easyocr
import numpy as np

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from PIL import Image

class EventType(Enum):
    NONE = 0
    ASSIST = 1
    KNOCK = 2
    SQUAD_WIPE = 3
    KNOCKED = 4
    VICTORY = 5

    @classmethod
    def from_str(cls, trigger: str) -> 'EventType':
        if trigger.lower() == 'assist':
            return cls.ASSIST
        elif trigger.lower() == 'knock':
            return cls.KNOCK
        elif trigger.lower() == 'squad-wipe':
            return cls.SQUAD_WIPE
        elif trigger.lower() == 'knocked':
            return cls.KNOCKED
        elif trigger.lower() == 'victory':
            return cls.VICTORY
        else:
            return cls.NONE


@dataclass
class GameEvent:
    type: EventType
    text: str

_ocr_reader = easyocr.Reader(['en'])


def from_file(image_file: Path) -> Image:
    return Image.open(image_file)


def detect_event(image: Image) -> list[GameEvent]:
    img_array = np.array(image)
    results = _ocr_reader.readtext(img_array)

    events = []
    for _, text, __ in results:
        if 'ASSIST' in text:
            events.append(GameEvent(EventType.ASSIST, text))
        elif 'KNOCKED DOWN' in text or 'RE-KNOCKED' in text:
            events.append(GameEvent(EventType.KNOCK, text))
        elif 'SQUAD WIPE' in text:
            events.append(GameEvent(EventType.SQUAD_WIPE, text))
        else:
            continue

    return events