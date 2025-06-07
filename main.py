import events
import recording_processor

import argparse
import logging

from manager import Manager
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)


def main(args):
    if args.image_file:
        img = events.from_file(args.image_file)
        img = img.crop((820, 960, 1100, 1000))
        img.show()
        print(events.detect_event(img))
    elif args.post_process:
        recording_processor.process_recording(args.post_process,
                                              [events.EventType.from_str(s) for s in args.replay_triggers])
    elif args.record:
        # Set up the Manager for recording and post-processing the recordings.
        manager = Manager(args.websocket_port, args.websocket_pass)
        manager.monitor_games(args.replay_triggers)
    else:
        manager = Manager(args.websocket_port, args.websocket_pass)
        manager.monitor_replay_triggers(args.replay_triggers)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OBS Apex Replay Trigger')
    parser.add_argument('--record', action='store_true', help='Monitor for match start/end and post-process recording')
    parser.add_argument('--post-process', type=Path, help='Post process recording and create highlight video')
    parser.add_argument("--websocket-port", default=4455, type=int, help="OBS WebSocket port")
    parser.add_argument("--websocket-pass", default='123456', type=str, help="OBS WebSocket password")
    parser.add_argument('--image-file', type=Path, help='Path of test input image to evaluate')
    parser.add_argument('-t', '--replay-triggers',
                        type=str,
                        nargs='*',
                        choices=['assist', 'knock', 'squad_wipe'],  # TODO: Add support for 'knocked' and 'victory'
                        default=['knock', 'squad_wipe'],
                        help='Triggers for saving replay buffer.')

    args = parser.parse_args()
    main(args)