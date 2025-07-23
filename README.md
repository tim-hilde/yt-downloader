# YouTube Downloader Service

A containerized YouTube downloader service that runs on Raspberry Pi using yt-dlp. The service accepts YouTube links via HTTP requests and queues them for sequential downloading.

## Features

- REST API for submitting YouTube download requests
- Queue system for managing multiple downloads
- Downloads videos at 1080p resolution when available
- Organizes downloads by playlist (if applicable)
- Runs in Docker container with file output to host system
- Health monitoring and status endpoints
- Optimized for Raspberry Pi

## Quick Start

1. **Clone and setup:**

   ```bash
   git clone <repository-url>
   cd yt-downloader
   ```

2. **Create downloads directory:**

   ```bash
   mkdir downloads
   ```

3. **Build and run with Docker Compose:**

   ```bash
   docker-compose up --build -d
   ```

4. **The service will be available at:** `http://localhost:5000`

## API Endpoints

### Submit Download Request

```bash
curl -X POST http://localhost:5000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

Response:

```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "queue_position": 1
}
```

### Check Overall Status

```bash
curl http://localhost:5000/status
```

### Check Specific Download

```bash
curl http://localhost:5000/download/{job_id}
```

### Health Check

```bash
curl http://localhost:5000/health
```

## File Organization

Downloads are saved to `./downloads/` with the following structure:

```
downloads/
├── Single Videos/
│   └── Video Title.mp4
└── Playlist Name/
    ├── 01_First Video.mp4
    ├── 02_Second Video.mp4
    └── ...
```

## yt-dlp Configuration

The service uses the following yt-dlp settings:

- **Quality:** Best available up to 1080p resolution
- **Format:** Best video + best audio, remuxed to MP4
- **Output template:** Organized by playlist with numbering
- **Additional features:** Metadata, thumbnails, and descriptions included

## Docker Configuration

### Environment Variables

- `PYTHONUNBUFFERED=1` - For real-time logging

### Volumes

- `./downloads:/downloads` - Mount host directory for downloads

### Ports

- `5000:5000` - Flask web service

## Development

### Local Development Setup

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install yt-dlp:

   ```bash
   pip install yt-dlp
   ```

3. Create downloads directory:

   ```bash
   mkdir downloads
   ```

4. Run the application:

   ```bash
   python app.py
   ```

### Docker Build Only

```bash
docker build -t yt-downloader .
docker run -d -p 5000:5000 -v $(pwd)/downloads:/downloads yt-downloader
```

## Raspberry Pi Deployment

1. **Ensure Docker is installed on your Raspberry Pi:**

   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd yt-downloader
   ```

3. **Start the service:**

   ```bash
   docker-compose up --build -d
   ```

4. **Monitor logs:**

   ```bash
   docker-compose logs -f
   ```

## Usage Examples

### Download a single video

```bash
curl -X POST http://raspberry-pi-ip:5000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Download a playlist

```bash
curl -X POST http://raspberry-pi-ip:5000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/playlist?list=PLxyz123"}'
```

### Check queue status

```bash
curl http://raspberry-pi-ip:5000/status | jq
```

## Troubleshooting

### Check container logs

```bash
docker-compose logs yt-downloader
```

### Check container health

```bash
docker-compose ps
```

### Restart service

```bash
docker-compose restart
```

### Update yt-dlp

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Security Notes

- The service runs as a non-root user inside the container
- Only YouTube URLs are accepted (validated via regex)
- Download timeout is set to 1 hour per video
- No authentication is implemented - consider adding if exposed to internet

## Customization

### Modify yt-dlp settings

Edit `config/yt-dlp-config` to change download behavior.

### Change output directory

Modify the volume mapping in `docker-compose.yml`:

```yaml
volumes:
  - /your/custom/path:/downloads
```

### Adjust quality settings

Edit the yt-dlp command in `app.py` to change resolution or format preferences.

## License

MIT License

