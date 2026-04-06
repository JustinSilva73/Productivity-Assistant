# CLAUDE.md - Productivity Assistant

## Project Overview

A Python voice assistant ("Jarvis") integrating speech recognition, task management, Spotify playback control, and OpenAI conversational AI. Uses Azure Cognitive Services for speech synthesis, Google Speech Recognition for transcription, and a MySQL database for persistence.

## Repository Structure

```
├── BackendRun.py              # Main entry point — spawns threads for voice, GUI, Flask
├── Base.py                    # Flask app factory and blueprint registration
├── VoiceAssistant.py          # Core assistant logic, phrase-to-function routing
├── PlayAudio.py               # Azure Speech SDK audio playback
├── phrases.json               # Voice command → function mappings
├── requirements.txt           # Python dependencies
├── Database/
│   ├── Base.py                # MySQL connection context manager
│   ├── CheckUser/LogIn.py     # bcrypt-based auth endpoint
│   └── StoreTranscriptions/   # Transcription persistence
├── OpenAI/
│   ├── Assistant.py           # JarvisAssistant (OpenAI Assistants API)
│   └── test/                  # Assistant and user input tests
├── Spotify/
│   ├── Connect.py             # SpotifyConnect — playback, auth, token refresh
│   ├── PlaylistBuilder/PlaylistAlgo.py  # Smart playlist management
│   └── test_connect.py        # Spotify connection tests
├── VoiceListen/
│   ├── Microphone.py          # Audio capture, noise reduction, transcription
│   └── test/                  # Mic and user mic tests
├── ToDo/
│   ├── ToDoList.py            # Database-backed task CRUD
│   └── DisplayList/DisplayList.py  # Tkinter GUI for tasks
├── Message/
│   └── receivedMessage.py     # /askJarvis Flask endpoint
└── test/                      # Top-level test package
```

## Tech Stack

- **Language**: Python 3.x
- **Web framework**: Flask with blueprints
- **Speech**: Azure Cognitive Services (synthesis), Google Speech Recognition (transcription)
- **AI**: OpenAI Assistants API
- **Database**: MySQL via PyMySQL
- **Music**: Spotify Web API (direct HTTP, OAuth 2.0)
- **GUI**: Tkinter (task display)
- **Audio**: PyAudio, noisereduce, numpy

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python BackendRun.py

# Run tests (pytest)
pytest test/
```

## Testing

- Framework: **pytest** (configured in `.vscode/settings.json`)
- Test locations:
  - `OpenAI/test/Assistant.test.py` — OpenAI assistant tests
  - `OpenAI/test/UserInputTest.py` — user input flow tests
  - `Spotify/test_connect.py` — Spotify API tests
  - `VoiceListen/test/MicTests.test.py` — microphone/audio tests
  - `VoiceListen/test/UserMicTest.py` — user mic integration tests

## Required Environment Variables

All loaded via `python-dotenv` from a `.env` file:

| Variable | Purpose |
|----------|---------|
| `SPEECH_KEY`, `SPEECH_REGION` | Azure Speech Services |
| `OPENAI_API_KEY`, `OPENAI_ASSISTANT_ID` | OpenAI Assistants API |
| `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` | Spotify OAuth |
| `SPOTIFY_USERNAME`, `SPOTIFY_PASSWORD` | Spotify account |
| `SPOTIPY_ACCESS_TOKEN`, `SPOTIPY_REFRESH_TOKEN` | Spotify tokens |
| `SPOTIFY_PLAYLIST`, `SPOTIFY_DEVICE_ID` | Spotify playback config |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | MySQL database |
| `SUCCESS_USER_ID`, `BCRYPT_ENCODING` | Authentication |

## Code Conventions

- **Classes**: PascalCase (`VoiceAssistant`, `SpotifyConnect`, `JarvisAssistant`)
- **Functions/methods**: snake_case (`add_task`, `get_response`)
- **Modules**: PascalCase filenames (`BackendRun.py`, `PlayAudio.py`)
- **Architecture**: Modular — each integration lives in its own directory
- **Database access**: Always use the context manager from `Database/Base.py`
- **Logging**: Use `logging` module; suppress noisy loggers (e.g., `urllib3`) at WARNING level
- **Config**: Voice commands defined in `phrases.json`, not hardcoded

## Architecture Notes

- **Threading model**: `BackendRun.py` spawns separate threads for async voice processing, Tkinter GUI event loop, and a GUI queue handler. Threads communicate via `queue.Queue`.
- **Voice activation**: Listens for activation words ("endeavor"/"jarvis") before processing commands.
- **Phrase routing**: `phrases.json` maps spoken phrases to method names; `fuzzywuzzy` provides fuzzy matching.
- **Spotify auth**: OAuth 2.0 with automatic token refresh via client credentials.
- **Playlist algorithm**: Tracks skip/completion ratios per song to intelligently manage playlist contents.
- **Flask API**: Two endpoints — `POST /askJarvis` (message relay) and `POST /login` (authentication).

## Known Considerations

- Volume control (`pycaw`) is Windows-only
- Discord integration (`DiscordTesting.py`) is experimental/abandoned
- System dependencies required: PortAudio (for PyAudio), Chrome (for Selenium auth flows)
- No CI/CD pipeline configured
