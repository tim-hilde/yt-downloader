import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import UrlInput from './components/UrlInput';
import QueueDisplay from './components/QueueDisplay';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function App() {
  const [queueData, setQueueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdateTime, setLastUpdateTime] = useState(0);

  const fetchQueueStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/status`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setQueueData(data);
      setError(null);
      setLastUpdateTime(Date.now());
    } catch (err) {
      console.error('Error fetching queue status:', err);
      setError('Failed to connect to the download service');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleUrlSubmit = async (url) => {
    try {
      const response = await fetch(`${API_BASE_URL}/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to add download');
      }

      const result = await response.json();
      
      // Refresh queue status immediately
      fetchQueueStatus();
      
      return { success: true, data: result };
    } catch (err) {
      console.error('Error submitting URL:', err);
      return { success: false, error: err.message };
    }
  };

  useEffect(() => {
    fetchQueueStatus();
    
    // Reduced polling frequency for Pi performance
    // Use adaptive polling - faster when downloading, slower when idle
    const setupPolling = () => {
      const hasActiveDownload = queueData?.current_download;
      const pollInterval = hasActiveDownload ? 3000 : 10000; // 3s when active, 10s when idle
      
      return setInterval(fetchQueueStatus, pollInterval);
    };
    
    const interval = setupPolling();
    
    return () => clearInterval(interval);
  }, [fetchQueueStatus, queueData?.current_download]);

  return (
    <div className="app">
      <header className="header">
        <h1>YouTube Downloader</h1>
        <p>Download videos and playlists from YouTube with ease. Simply paste a URL.</p>
      </header>

      <main>
        <UrlInput onUrlSubmit={handleUrlSubmit} />
        
        {error && (
          <div className="status-message status-error">
            {error}
          </div>
        )}
        
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        ) : (
          <QueueDisplay data={queueData} />
        )}
      </main>
    </div>
  );
}

export default App;
