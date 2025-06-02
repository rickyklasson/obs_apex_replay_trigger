import datetime
import events
import screen

import obsws_python as obs

import time


class Manager:
    TRIGGER_DELAY = 10  # Delay to wait for further events before saving replay buffer.

    def __init__(self, triggers: list[str], websocket_port: int, websocket_pass: str):
        self.obs_client = obs.ReqClient(host='localhost', port=websocket_port, password=websocket_pass, timeout=3)
        self.replay_triggers = [events.EventType.from_str(s) for s in triggers]

        print('Starting replay buffer')
        self.obs_client.start_replay_buffer()

    def run(self):
        try:
            print('Starting game event detection')
            last_event_time = None
            while True:
                start_time = time.time()

                # Capture image.
                img = screen.grab_screen_event_region()

                # Detect event.
                game_events = events.detect_event(img)

                for ev in game_events:
                    print(f'Game event: {ev} detected at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

                    if ev.type in self.replay_triggers:
                        last_event_time = time.time()
                        print(f'Last event time: {last_event_time:.1f}')
                        break

                if last_event_time is not None and time.time() - last_event_time > self.TRIGGER_DELAY:
                    print(f'Event delay passed. Saving replay buffer!')
                    self.obs_client.save_replay_buffer()
                    last_event_time = None

                # Sleep.
                end_time = time.time()
                print(f'Ran in: {end_time - start_time:.3f}s', end='\r', flush=True)
                time.sleep(max(0, 0.5 - (end_time - start_time)))

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f'Exception occurred: {e}')
        finally:
            self.obs_client.stop_replay_buffer()
            time.sleep(0.2)
            self.obs_client.disconnect()
            print('Stopping replay buffer and disconnecting websocket, exiting...')