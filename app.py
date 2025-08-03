#!/usr/bin/env python3

import logging
import os
import queue
import re
import subprocess
import threading
import time
import uuid
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global queue and status tracking
download_queue = queue.Queue()
# Use OrderedDict with size limit for memory management
MAX_STORED_JOBS = 100
download_status = OrderedDict()
current_download = None
worker_thread = None

# Rate limiting
last_request_times = {}
RATE_LIMIT_WINDOW = 5  # seconds


class DownloadJob:
    def __init__(self, url, job_id=None):
        self.url = url
        self.id = job_id or str(uuid.uuid4())
        self.status = "queued"
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.output = None
        # Progress tracking
        self.progress = {
            "percent": 0,
            "speed": None,
            "eta": None,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "filename": None,
        }
        self.progress_lock = threading.Lock()

    def update_progress(self, progress_data):
        """Thread-safe progress update"""
        with self.progress_lock:
            self.progress.update(progress_data)


def is_valid_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    youtube_regex = re.compile(
        r"(https?://)?(www\.)?(m\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/"
        r"(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    )
    return youtube_regex.match(url) is not None


def parse_progress_line(line):
    """Parse yt-dlp progress output line"""
    progress_data = {}

    # Pattern for download progress: [download]  45.2% of 1.23GiB at 2.34MiB/s ETA 00:05:23
    download_pattern = r"\[download\]\s+(\d+\.?\d*)%\s+of\s+([\d\.]+\w+)?\s*(?:at\s+([\d\.]+\w+/s))?\s*(?:ETA\s+(\d+:\d+:\d+))?"
    match = re.search(download_pattern, line)

    if match:
        progress_data["percent"] = float(match.group(1))
        if match.group(2):
            progress_data["total_size"] = match.group(2)
        if match.group(3):
            progress_data["speed"] = match.group(3)
        if match.group(4):
            progress_data["eta"] = match.group(4)

    # Pattern for filename: [download] Destination: filename.mp4
    filename_pattern = r"\[download\] Destination: (.+)"
    filename_match = re.search(filename_pattern, line)
    if filename_match:
        progress_data["filename"] = filename_match.group(1).split("/")[
            -1
        ]  # Just the filename

    return progress_data


def download_worker():
    """Background worker that processes the download queue"""
    global current_download

    while True:
        try:
            # Get next job from queue (blocks until available)
            job = download_queue.get()
            current_download = job

            logger.info(f"Starting download for job {job.id}: {job.url}")
            job.status = "downloading"
            job.started_at = datetime.now()

            # Prepare yt-dlp command
            cmd = [
                "yt-dlp",
                "-S",
                "res:1080",
                "-f",
                "bestvideo+bestaudio",
                "--remux-video",
                "mp4",
                "--config-location",
                "/app/config/yt-dlp-config",
                "--progress",  # Enable progress output
                job.url,
            ]

            # Execute download
            try:
                # Start process with real-time output capture
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd="/downloads",
                    bufsize=1,
                    universal_newlines=True,
                )

                output_lines = []

                # Read output line by line for real-time progress
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break

                    if line:
                        line = line.strip()
                        output_lines.append(line)

                        # Parse progress information
                        progress_data = parse_progress_line(line)
                        if progress_data:
                            job.update_progress(progress_data)
                            logger.debug(
                                f"Progress update for job {job.id}: {progress_data}"
                            )

                # Wait for process to complete
                return_code = process.wait(timeout=3600)  # 1 hour timeout

                if return_code == 0:
                    job.status = "completed"
                    job.output = "\n".join(output_lines)
                    # Set final progress to 100%
                    job.update_progress({"percent": 100})
                    logger.info(f"Successfully completed download for job {job.id}")
                else:
                    job.status = "failed"
                    job.error = "\n".join(output_lines)
                    logger.error(f"Download failed for job {job.id}: {job.error}")

            except subprocess.TimeoutExpired:
                job.status = "failed"
                job.error = "Download timeout (1 hour limit exceeded)"
                logger.error(f"Download timeout for job {job.id}")
                try:
                    process.kill()
                except:
                    pass

            except Exception as e:
                job.status = "failed"
                job.error = str(e)
                logger.error(f"Download error for job {job.id}: {str(e)}")

            job.completed_at = datetime.now()
            current_download = None

            # Mark task as done
            download_queue.task_done()

        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            current_download = None


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "queue_size": download_queue.qsize(),
            "current_download": current_download.id if current_download else None,
        }
    )


@app.route("/download", methods=["POST"])
def add_download():
    """Add a YouTube URL to the download queue"""
    try:
        data = request.get_json()

        if not data or "url" not in data:
            return jsonify({"error": "URL is required"}), 400

        url = data["url"].strip()

        # Validate YouTube URL
        if not is_valid_youtube_url(url):
            return jsonify({"error": "Invalid YouTube URL"}), 400

        # Create download job
        job = DownloadJob(url)
        download_status[job.id] = job

        # Add to queue
        download_queue.put(job)

        logger.info(f"Added download job {job.id} for URL: {url}")

        return jsonify(
            {
                "job_id": job.id,
                "status": job.status,
                "url": job.url,
                "queue_position": download_queue.qsize(),
            }
        ), 201

    except Exception as e:
        logger.error(f"Error adding download: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/status", methods=["GET"])
def get_status():
    """Get overall queue status"""
    try:
        # Get recent jobs (last 50)
        recent_jobs = []
        for job_id, job in list(download_status.items())[-50:]:
            job_data = {
                "job_id": job.id,
                "url": job.url,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat()
                if job.completed_at
                else None,
                "error": job.error,
            }

            # Add progress data if downloading
            if job.status == "downloading":
                with job.progress_lock:
                    job_data["progress"] = job.progress.copy()

            recent_jobs.append(job_data)

        current_download_data = None
        if current_download:
            current_download_data = {
                "job_id": current_download.id,
                "url": current_download.url,
                "started_at": current_download.started_at.isoformat(),
            }
            # Add progress data
            with current_download.progress_lock:
                current_download_data["progress"] = current_download.progress.copy()

        return jsonify(
            {
                "queue_size": download_queue.qsize(),
                "current_download": current_download_data,
                "recent_jobs": recent_jobs,
            }
        )

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/download/<job_id>", methods=["GET"])
def get_download_status(job_id):
    """Get status of a specific download job"""
    try:
        if job_id not in download_status:
            return jsonify({"error": "Job not found"}), 404

        job = download_status[job_id]

        job_data = {
            "job_id": job.id,
            "url": job.url,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
            "output": job.output,
        }

        # Add progress data if downloading
        if job.status == "downloading":
            with job.progress_lock:
                job_data["progress"] = job.progress.copy()

        return jsonify(job_data)

    except Exception as e:
        logger.error(f"Error getting download status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


def start_worker():
    """Start the background worker thread"""
    global worker_thread
    worker_thread = threading.Thread(target=download_worker, daemon=True)
    worker_thread.start()
    logger.info("Download worker thread started")


if __name__ == "__main__":
    # Ensure downloads directory exists
    os.makedirs("/downloads", exist_ok=True)

    # Start background worker
    start_worker()

    # Start Flask app
    app.run(host="0.0.0.0", port=5000, debug=False)
