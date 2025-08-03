import React, { memo } from 'react';

const JobItem = memo(({ job, isCurrent = false }) => {
  const formatTime = (timestamp) => {
    if (!timestamp) return null;
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatUrl = (url) => {
    try {
      const urlObj = new URL(url);
      if (urlObj.hostname.includes('youtube.com') || urlObj.hostname.includes('youtu.be')) {
        return url.length > 60 ? url.substring(0, 60) + '...' : url;
      }
      return url;
    } catch {
      return url.length > 60 ? url.substring(0, 60) + '...' : url;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'queued':
        return 'status-indicator status-queued';
      case 'downloading':
        return 'status-indicator status-downloading';
      case 'completed':
        return 'status-indicator status-completed';
      case 'failed':
        return 'status-indicator status-failed';
      default:
        return 'status-indicator';
    }
  };

  const getDuration = () => {
    if (!job.started_at) return null;
    
    const start = new Date(job.started_at);
    const end = job.completed_at ? new Date(job.completed_at) : new Date();
    const duration = Math.floor((end - start) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  const renderProgressBar = () => {
    if (job.status !== 'downloading' || !job.progress) return null;
    
    const { percent = 0, speed, eta, filename } = job.progress;
    
    return (
      <div className="progress-container">
        {filename && (
          <div className="progress-filename">
            📁 {filename}
          </div>
        )}
        <div className="progress-bar-container">
          <div className="progress-bar">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${Math.min(percent, 100)}%` }}
            />
          </div>
          <div className="progress-text">
            {percent.toFixed(1)}%
          </div>
        </div>
        <div className="progress-details">
          {speed && (
            <div className="progress-speed">
              🚀 {speed}
            </div>
          )}
          {eta && (
            <div className="progress-eta">
              ⏱️ ETA: {eta}
            </div>
          )}
        </div>
      </div>
    );
  };
  return (
    <div className={`job-item ${isCurrent ? 'current-job' : ''}`}>
      <div className="job-header">
        <div className="job-url" title={job.url}>
          {formatUrl(job.url)}
        </div>
        <div className={`job-status ${job.status}`}>
          <span className={getStatusColor(job.status)}></span>
          {job.status}
        </div>
      </div>
      
      {renderProgressBar()}
      
      <div className="job-meta">
        <div className="job-time">
          <span>Created:</span>
          <span>{formatTime(job.created_at)}</span>
        </div>
        
        {job.started_at && (
          <div className="job-time">
            <span>Started:</span>
            <span>{formatTime(job.started_at)}</span>
          </div>
        )}
        
        {job.completed_at && (
          <div className="job-time">
            <span>Completed:</span>
            <span>{formatTime(job.completed_at)}</span>
          </div>
        )}
        
        {getDuration() && (
          <div className="job-time">
            <span>Duration:</span>
            <span>{getDuration()}</span>
          </div>
        )}
        
        <div className="job-id">
          ID: {job.job_id}
        </div>
      </div>
      
      {job.error && (
        <div className="error-message">
          {job.error}
        </div>
      )}
    </div>
  );
};

export default JobItem;