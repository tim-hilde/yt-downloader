# YouTube Downloader Frontend

A clean, minimal React frontend for the YouTube downloader service.

## Features

- **Clean Design**: Apple-inspired minimal interface with Lumon aesthetics
- **Real-time Updates**: Auto-refreshes queue status every 3 seconds
- **Queue Management**: View current downloads, queue status, and recent jobs
- **Responsive Design**: Works on desktop and mobile devices
- **Status Indicators**: Visual indicators for different download states

## Development

### Local Development

```bash
cd frontend
npm install
npm start
```

The app will be available at `http://localhost:3000`.

### Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: `http://localhost:5001`)

### Docker

The frontend is containerized and included in the main docker-compose setup. It runs on port 3000.

## Design Philosophy

The interface follows a minimal, clean design inspired by Apple's design language and the Lumon aesthetic from Severance:

- **Typography**: System fonts for native feel
- **Colors**: Subtle grays, whites, and accent blues
- **Spacing**: Generous whitespace for breathing room
- **Interactions**: Smooth transitions and hover states
- **Status**: Clear visual indicators for different states

## Components

- **App**: Main application component with state management
- **UrlInput**: Form for submitting YouTube URLs
- **QueueDisplay**: Shows queue statistics and job list
- **JobItem**: Individual job display with status and metadata