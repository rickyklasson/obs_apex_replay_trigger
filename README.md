# OBS Apex Replay Trigger

A Python tool for live analysis of Apex Legends gameplay.
It uses OCR to detect in-game events from the screen and triggers the OBS replay buffer via the OBS WebSocket API.

## Features
- Screen region capture and OCR event detection
- Configurable event triggers (assist, knock, squad-wipe, etc.)
- Automatic replay buffer saving in OBS Studio

## Usage
1. Install requirements: `pip install -r requirements.txt`
2. Start OBS Studio with obs-websocket enabled.
3. Run: `python main.py [options]`