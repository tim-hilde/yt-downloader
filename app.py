#!/usr/bin/env python3

import logging
import os
import queue
import re
import subprocess
import threading
import time
import uuid
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global queue and status tracking
download_queue = queue.Queue()
download_status = {}
current_download = None
worker_thread = None


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


def is_valid_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    youtube_regex = re.compile(
        r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/"
        r"(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    )
    return youtube_regex.match(url) is not None


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
                job.url,
            ]

            # Execute download
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd="/downloads",
                    timeout=3600,  # 1 hour timeout
                )

                if result.returncode == 0:
                    job.status = "completed"
                    job.output = result.stdout
                    logger.info(f"Successfully completed download for job {job.id}")
                else:
                    job.status = "failed"
                    job.error = result.stderr
                    logger.error(f"Download failed for job {job.id}: {result.stderr}")

            except subprocess.TimeoutExpired:
                job.status = "failed"
                job.error = "Download timeout (1 hour limit exceeded)"
                logger.error(f"Download timeout for job {job.id}")

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
            recent_jobs.append(
                {
                    "job_id": job.id,
                    "url": job.url,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat()
                    if job.started_at
                    else None,
                    "completed_at": job.completed_at.isoformat()
                    if job.completed_at
                    else None,
                    "error": job.error,
                }
            )

        return jsonify(
            {
                "queue_size": download_queue.qsize(),
                "current_download": {
                    "job_id": current_download.id,
                    "url": current_download.url,
                    "started_at": current_download.started_at.isoformat(),
                }
                if current_download
                else None,
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

        return jsonify(
            {
                "job_id": job.id,
                "url": job.url,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat()
                if job.completed_at
                else None,
                "error": job.error,
                "output": job.output,
            }
        )

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

