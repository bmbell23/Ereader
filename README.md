# Ereader

A custom ereader Android app that connects to your Calibre library. Built because all other ereader apps suck.

## Features

- 📚 **Calibre Integration** - Direct access to your Calibre Content Server
- 🏷️ **Full Metadata** - Authors, series, tags, cover art, descriptions
- ⬇️ **Download to phone** - Save books locally for offline reading
- 📖 **PDF Reader** - Clean, simple PDF reading experience
- 🌐 **VPN-ready** - Works over local network or VPN
- 🔮 **Future-proof** - Designed with web interface in mind

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Android App    │◄────────┤  Flask Backend   │◄────────┤ Calibre Content  │
│  (React Native) │  HTTP   │  (API Proxy)     │  HTTP   │     Server       │
│                 │         │                  │         │                  │
│  Local Storage  │         │                  │         │  Calibre Library │
└─────────────────┘         └──────────────────┘         └──────────────────┘
```

**Backend**: Flask REST API that proxies and enhances Calibre's API
**Calibre**: Your existing Calibre Content Server with all your books and metadata
**Frontend**: React Native Android app (with future web support in mind)

## Quick Start

👉 **See [QUICKSTART.md](QUICKSTART.md) for step-by-step instructions**

### TL;DR

1. Start backend (connects to your Calibre server):
   ```bash
   cd backend
   ./run.sh
   ```

2. Build the Android app:
   ```bash
   ./build-app.sh
   ```

3. Install APK on your phone (via ADB or HTTP)

4. Configure server URL in app settings

5. Start reading!

## Requirements

### Linux Server
- Python 3.7+
- Calibre Content Server (already running on port 8083)
- Your Calibre library

### For Building
- Node.js 18+
- Android SDK or Android Studio
- JDK 17

### For Running
- Android phone (API 24+ / Android 7.0+)
- Both devices on same network/VPN

## Project Structure

```
Ereader/
├── backend/           # Flask server
│   ├── server.py      # Main API server
│   ├── requirements.txt
│   └── run.sh
├── app/              # React Native app
│   ├── android/      # Android-specific code
│   ├── src/          # App source code
│   │   ├── screens/  # UI screens
│   │   ├── App.js    # Main app component
│   │   └── config.js # Configuration
│   └── package.json
├── build-app.sh      # Automated build script
├── QUICKSTART.md     # Quick start guide
└── SETUP.md          # Detailed setup instructions
```

## Supported Formats

| Format | Status |
|--------|--------|
| PDF    | ✅ Supported |
| EPUB   | 🔜 Coming soon |
| MOBI   | 🔜 Coming soon |
| AZW3   | 🔜 Planned |

## API Endpoints

The backend server provides:

- `GET /api/books` - List all books
- `GET /api/books/<id>` - Get book info
- `GET /api/books/<id>/download` - Download book
- `GET /api/health` - Health check

## Development

### Backend Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export BOOKS_DIR="/path/to/books"
python server.py
```

### App Development
```bash
cd app
npm install
npm start  # Start Metro bundler
npm run android  # Run on connected device
```

## Future Plans

- [ ] EPUB reader support
- [ ] Reading progress tracking across devices
- [ ] Bookmarks and highlights
- [ ] Web interface for desktop reading
- [ ] Night mode / custom themes
- [ ] Font size and style customization
- [ ] Collections/categories
- [ ] Search functionality
- [ ] Book metadata editing

## Why Build This?

Because every ereader app out there either:
- Locks you into an ecosystem
- Has terrible UX
- Doesn't support your own library
- Costs money for basic features
- Harvests your data

This is YOUR library, YOUR app, YOUR way.

## License

MIT - Do whatever you want with it

## Contributing

Feel free to fork, modify, and make it your own!

## Troubleshooting

See [SETUP.md](SETUP.md) for detailed troubleshooting.

Common issues:
- **Can't connect**: Check VPN/network and firewall
- **Build fails**: Verify JDK 17 and Android SDK installation
- **No books**: Check BOOKS_DIR path and file permissions
