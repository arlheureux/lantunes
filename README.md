# LanTunes

A self-hosted LAN music streaming server with multi-client sync, authentication, and device casting.

## Features

- **Web Interface** - Beautiful, responsive UI for desktop and mobile
- **Lossless Audio** - FLAC, ALAC, WAV, and other lossless formats
- **M4A/AAC Support** - Automatic transcoding for browser compatibility  
- **Multi-Client Sync** - All connected devices stay in sync via WebSockets
- **Device Casting** - "Play To" feature to send audio to a specific device
- **Authentication** - User management with admin approval workflow
- **Library Management** - Automatic scanning with metadata extraction
- **Playlists** - Create and manage playlists
- **Search** - Search across tracks, albums, and artists
- **Shuffle Play** - Random playback mode

## Requirements

- Python 3.8+
- FFmpeg (for M4A transcoding)

## Installation

### Quick Start

```bash
git clone https://github.com/arlheureux/lantunes.git
cd lantunes
python3 run.py
```

The server will:
1. Create a virtual environment with all dependencies
2. Start the server on http://0.0.0.0:8080
3. Open http://localhost:8080 in your browser

### First-Time Setup

1. Open http://localhost:8080 - you'll be redirected to login
2. Click "Create Admin Account" to set up your first admin user
3. After login, go to Settings and set your music path
4. Click "Scan Library" to index your music

### For Other Devices on Your Network

Access from any device on your LAN:
```
http://<your-server-ip>:8080
```

## User Management

### Registration Flow
1. Users register through the login page
2. New users start with "pending" status
3. Admin must approve users before they can login
4. Approved users can access the full application

### Admin Tasks
- View all users in Settings
- Approve pending users
- Delete/reject users

## Cast Play To

When multiple devices are connected:
1. Select which device should play audio from the dropdown in the player bar
2. Click play on any device - audio will stream to the selected device
3. The other devices act as remote controls

## API Endpoints

### Authentication
- `POST /api/auth/setup` - Create first admin (only when no users exist)
- `POST /api/auth/register` - Register new user (requires approval)
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

### User Management (Admin)
- `GET /api/auth/users` - List all users
- `POST /api/auth/users/{id}/approve` - Approve user
- `DELETE /api/auth/users/{id}` - Delete user

### Library
- `GET /api/library/tracks` - List tracks
- `GET /api/library/albums` - List albums
- `GET /api/library/artists` - List artists
- `GET /api/library/search?q=` - Search
- `POST /api/library/scan` - Scan library

### Playback
- `GET /api/playback/state` - Get playback state
- `POST /api/playback/play` - Play track
- `POST /api/playback/pause` - Pause
- `POST /api/playback/next` - Next track
- `POST /api/playback/previous` - Previous track
- `POST /api/playback/seek?position=` - Seek
- `GET /api/playback/stream/{id}` - Stream audio

### WebSocket
- `WS /ws` - Real-time sync for playback state and device management

## Configuration

Edit `config.yaml` to customize settings:

```yaml
library:
  music_path: "/path/to/your/music"
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development
cd backend
python main.py
```

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: Vue.js 3, Font Awesome
- **Database**: SQLite
- **Audio**: FFmpeg for transcoding