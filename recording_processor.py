import events
import screen

import io
import json
import logging
import subprocess

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image


@dataclass
class VideoMetadata:
    path: Path
    duration: float
    framerate: float
    width: int
    height: int
    start_time: datetime
    end_time: datetime

    @classmethod
    def from_path(cls, video_path: Path) -> 'VideoMetadata':
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v",
            "-show_entries", "format=duration",
            "-show_entries", "stream=r_frame_rate,width,height",
            "-of", "json",
            str(video_path),
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise ChildProcessError('Failed ffprobe command')

        ffprobe_data = json.loads(result.stdout)

        stream = ffprobe_data['streams'][0]
        framerate_str = stream['r_frame_rate']
        num, den = framerate_str.split('/', maxsplit=1)
        framerate = float(num) / float(den)

        duration = float(ffprobe_data['format']['duration'])
        end_time = datetime.strptime(video_path.stem, "%Y-%m-%d_%H-%M-%S")
        start_time = end_time - timedelta(seconds=duration)

        return cls(path=video_path,
                   duration=duration,
                   framerate=framerate,
                   width=int(stream['width']),
                   height=int(stream['height']),
                   start_time=start_time,
                   end_time=end_time)


def _extract_event_timestamps(rec_metadata: VideoMetadata, event_triggers: list[events.EventType]) -> list[int]:
    """Extracts timestamps of game events."""
    logging.info('Extracting game event timestamps.')

    FPS = 1
    ffmpeg_command = [
        "ffmpeg",
        "-i", str(rec_metadata.path),
        "-vf", f"fps={FPS}",
        "-f", "image2pipe",
        "-vcodec", "png",
        "-"
    ]

    proc = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    timestamps = []
    timestamp = 0
    while True:
        print(f'Analysing image at timestamp: {timestamp}', end='\r', flush=True)

        # Read JPEG frame from stdout.
        png_header = proc.stdout.read(8)
        if not png_header:
            break

        if png_header != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Invalid PNG header")

        # Read PNG chunks until IEND is found
        data = bytearray(png_header)
        while True:
            chunk_len = int.from_bytes(proc.stdout.read(4), "big")
            chunk_type = proc.stdout.read(4)
            chunk_data = proc.stdout.read(chunk_len)
            crc = proc.stdout.read(4)

            data.extend(chunk_len.to_bytes(4, "big"))
            data.extend(chunk_type)
            data.extend(chunk_data)
            data.extend(crc)

            if chunk_type == b"IEND":
                break

        img = Image.open(io.BytesIO(data))
        img = screen.crop_to_region(img, 'player_event')
        event = events.detect_event(img)
        if event.type in event_triggers:
            timestamps.append(timestamp)

        timestamp += FPS

    logging.info(f'Found {len(timestamps)} event(s) in game recording.')

    return timestamps


def _timestamps_to_highlights(timestamps: list[int]) -> list[tuple]:
    """
    Given a sorted list of event timestamps (in seconds), merge close events into highlight periods.
    Each period starts 20s before the first event and ends 5s after the last event in a group.
    If the next event is within 20s, extend the period to include it.
    Returns a list of (start, end) tuples (in seconds).
    """
    if not timestamps:
        return []

    highlights = []
    start = max(0, timestamps[0] - 20)
    end = timestamps[0] + 5

    for i in range(1, len(timestamps)):
        if timestamps[i] - timestamps[i - 1] < 20:
            # Extend the current highlight period.
            end = timestamps[i] + 5
        else:
            # Save the current period and start a new one.
            highlights.append((start, end))
            start = max(0, timestamps[i] - 20)
            end = timestamps[i] + 5

    highlights.append((start, end))

    logging.info(f'Converted {len(timestamps)} game event(s) to {len(highlights)} highlight section(s).')
    return highlights


def _create_highlight(metadata: VideoMetadata, highlights: list[tuple[int, int]]):
    """
    Create a highlight video from the original, keeping highlight periods at 1x speed with audio,
    and speeding up (10x) and silencing audio in non-highlight periods.
    """
    logging.info('Assembling highlight video.')

    input_path = str(metadata.path)

    # Extract and process segments
    output_path = metadata.path.parent / f'Highlights_{metadata.path.stem}.mkv'
    segment_files = []
    for i, (start, end) in enumerate(highlights):
        seg_file = output_path.parent / f"segment_{i}.mp4"
        segment_files.append(seg_file)
        duration = end - start
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            "-v", "quiet",
            "-stats",
            str(seg_file)
        ]
        print(f'Encoding segment {i} with command:\n {" ".join(cmd)}')
        subprocess.run(cmd, check=True)

    # Create concat file
    concat_file = output_path.parent / "concat_segments.txt"
    with open(concat_file, "w") as f:
        for seg_file in segment_files:
            f.write(f"file '{seg_file.resolve()}'\n")

    # Concatenate segments
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path)
    ]
    subprocess.run(cmd_concat, check=True)

    # Clean up segment files
    for seg_file in segment_files:
        seg_file.unlink()
    concat_file.unlink()

    logging.info(f'Highlight video written to: {output_path}')


def process_recording(rec: Path, event_triggers: list[events.EventType]):
    logging.info(f'Processing recording: {rec}')

    rec_metadata = VideoMetadata.from_path(rec)
    event_timestamps = _extract_event_timestamps(rec_metadata, event_triggers)

    highlights = _timestamps_to_highlights(event_timestamps)

    if not highlights:
        return

    _create_highlight(rec_metadata, highlights)
