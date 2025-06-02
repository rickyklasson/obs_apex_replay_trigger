import argparse
import events

from manager import Manager
from pathlib import Path


def main(args):
    if args.image_file:
        img = events.from_file(args.image_file)
        img = img.crop((600, 760, 1320, 795))
        events.detect_event(img)
    else:
        manager = Manager(args.replay_triggers, args.websocket_port, args.websocket_pass)
        manager.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OBS Apex Replay Trigger')
    parser.add_argument("--websocket-port", default=4455, type=int, help="OBS WebSocket port")
    parser.add_argument("--websocket-pass", default='123456', type=str, help="OBS WebSocket password")
    parser.add_argument('--image-file', type=Path, help='Path of test input image to evaluate.')
    parser.add_argument('-t', '--replay-triggers',
                        type=str,
                        nargs='*',
                        choices=['assist', 'knock', 'squad-wipe'],  # TODO: Add support for 'knocked' and 'victory'
                        default=['knock', 'squad-wipe'],
                        help='Triggers for saving replay buffer.')

    args = parser.parse_args()
    main(args)