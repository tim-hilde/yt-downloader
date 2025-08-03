import React, { memo } from 'react';
import JobItem from './JobItem';

const QueueDisplay = memo(({ data }) => {
  if (!data) {
    return (
      <div className="queue-container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  const { queue_size, current_download, recent_jobs = [] } = data;
  
  // Filter out current download from recent jobs to avoid duplication
  const filteredRecentJobs = current_download 
    ? recent_jobs.filter(job => job.job_id !== current_download.job_id)
    : recent_jobs;

  // Count jobs by status
  const statusCounts = filteredRecentJobs.reduce((acc, job) => {
    acc[job.status] = (acc[job.status] || 0) + 1;
    return acc;
  }, {});

  // Add current download to counts if it exists
  if (current_download) {
    statusCounts.downloading = (statusCounts.downloading || 0) + 1;
  }

  const totalJobs = filteredRecentJobs.length;
  const hasJobs = totalJobs > 0 || current_download;

  return (
    <div className="queue-container">
      <div className="queue-header">
        <h2 className="queue-title">Download Queue</h2>
        <div className="queue-stats">
          <div className="queue-stat">
            <span className="status-indicator status-queued"></span>
            <span>{queue_size} queued</span>
          </div>
          {current_download && (
            <div className="queue-stat">
              <span className="status-indicator status-downloading"></span>
              <span>1 downloading</span>
            </div>
          )}
          <div className="queue-stat">
            <span className="status-indicator status-completed"></span>
            <span>{statusCounts.completed || 0} completed</span>
          </div>
          {statusCounts.failed > 0 && (
            <div className="queue-stat">
              <span className="status-indicator status-failed"></span>
              <span>{statusCounts.failed} failed</span>
            </div>
          )}
        </div>
      </div>

      {!hasJobs ? (
        <div className="empty-state">
          <h3>No downloads yet</h3>
          <p>Add a YouTube URL above to start downloading videos and playlists.</p>
        </div>
      ) : (
        <div className="jobs-list">
          {/* Current download section */}
          {current_download && (
            <>
              <div className="section-header">
                <h3>Currently Downloading</h3>
              </div>
              <div className="current-download-section">
                <JobItem 
                  job={{
                    ...current_download,
                    status: 'downloading'
                  }}
                  isCurrent={true}
                />
              </div>
            </>
          )}
          
          {/* Recent jobs section */}
          {filteredRecentJobs.length > 0 && (
            <>
              <div className="section-header">
                <h3>Recent Downloads</h3>
              </div>
              <div className="recent-jobs-section">
                {filteredRecentJobs
                  .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                  .map((job) => (
                    <JobItem key={job.job_id} job={job} />
                  ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default QueueDisplay;