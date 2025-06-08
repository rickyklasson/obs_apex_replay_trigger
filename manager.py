import datetime
import events
import logging
import recording_processor as rec_proc
import screen
import sys

from enum import Enum
from pathlib import Path

import obsws_python as obs

import time


class Manager:
    TRIGGER_DELAY = 15  # Delay to wait for further events before saving replay buffer.

    def __init__(self, websocket_port: int, websocket_pass: str):
        self.obs_client = obs.ReqClient(host='localhost', port=websocket_port, password=websocket_pass, timeout=3)

    def _get_last_recorded_file(self) -> Path | None:
        record_dir = Path(self.obs_client.get_record_directory().record_directory)

        files = [f for f in record_dir.iterdir() if f.is_file()]
        if not files:
            return None

        last_file = max(files, key=lambda f: f.stat().st_ctime)
        return last_file

    def monitor_replay_triggers(self, triggers: list[str]):
        PERIOD = 0.75
        replay_triggers = [events.EventType.from_str(s) for s in triggers]

        try:
            logging.info('Starting replay buffer monitor!')
            self.obs_client.start_replay_buffer()

            last_event_time = None
            while True:
                start_time = time.time()

                # Capture image.
                img = screen.grab_region('player_event')

                # Detect event.
                event = events.detect_event(img)

                if event is not None:
                    logging.debug(f'Game event: {event} detected at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

                    if event.type in replay_triggers:
                        last_event_time = time.time()
                        logging.debug(f'Last event time: {last_event_time:.1f}')

                if last_event_time is not None and time.time() - last_event_time > self.TRIGGER_DELAY:
                    logging.info(f'Event delay passed. Saving replay buffer!')
                    self.obs_client.save_replay_buffer()
                    last_event_time = None

                # Sleep.
                end_time = time.time()
                time.sleep(max(0, PERIOD - (end_time - start_time)))

        except KeyboardInterrupt:
            pass
        except Exception as e:
            logging.error(f'Exception occurred: {e}')
        finally:
            self.obs_client.stop_replay_buffer()
            time.sleep(0.2)
            self.obs_client.disconnect()
            logging.info('Stopping replay buffer and disconnecting websocket, exiting...')

    def monitor_games(self, triggers: list[str]):
        PERIOD = 1.0

        class State(Enum):
            WAITING_FOR_GAME = 0
            RECORDING = 1
            PROCESS_RECORDING = 2

        state = State.WAITING_FOR_GAME
        count = 0
        try:
            logging.info('Starting game monitor!')
            while True:
                start_time = time.time()

                if state == State.WAITING_FOR_GAME:
                    img = screen.grab_region('game_start')
                    event = events.detect_event(img)
                    if event.type == events.EventType.GAME_START:
                        logging.info('Game start detected, starting recording!')

                        # Initiate OBS recording.
                        self.obs_client.start_record()
                        state = State.RECORDING
                elif state == State.RECORDING:
                    # Check for game end and victory every other time.
                    if count % 2 == 0:
                        img = screen.grab_region('game_end')
                    else:
                        img = screen.grab_region('victory')

                    event = events.detect_event(img)
                    if event.type in [events.EventType.GAME_END, events.EventType.VICTORY]:
                        logging.info('Game end detected, stopping recording!')
                        self.obs_client.stop_record()

                        state = State.PROCESS_RECORDING
                elif state == State.PROCESS_RECORDING:
                    recorded_file = self._get_last_recorded_file()
                    assert recorded_file is not None

                    replay_triggers = [events.EventType.from_str(s) for s in triggers]
                    rec_proc.process_recording(recorded_file, replay_triggers)

                    logging.info('Recording processed! Waiting for new game...')
                    state = State.WAITING_FOR_GAME

                # Sleep.
                end_time = time.time()
                logging.debug(f'({state}) Ran in: {end_time - start_time:.3f}s')
                time.sleep(max(0, PERIOD - (end_time - start_time)))

        except KeyboardInterrupt:
            pass
        finally:
            self.obs_client.disconnect()
            print('Stopping game monitor and disconnecting websocket, exiting...')