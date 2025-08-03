import React, { useState, useCallback } from 'react';

const UrlInput = ({ onUrlSubmit }) => {
  const [url, setUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  // Debounced URL change to reduce re-renders
  const handleUrlChange = useCallback((e) => {
    setUrl(e.target.value);
    // Clear any existing error message when user starts typing
    if (message?.type === 'error') {
      setMessage(null);
    }
  }, [message?.type]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    
    if (!url.trim()) {
      setMessage({ type: 'error', text: 'Please enter a YouTube URL' });
      return;
    }

    setIsSubmitting(true);
    setMessage(null);

    try {
      const result = await onUrlSubmit(url.trim());
      
      if (result.success) {
        setUrl('');
        setMessage({ 
          type: 'success', 
          text: `Download added to queue! Job ID: ${result.data.job_id}` 
        });
        
        // Clear message after 5 seconds
        setTimeout(() => setMessage(null), 5000);
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'An unexpected error occurred' });
    } finally {
      setIsSubmitting(false);
    }
  }, [url, onUrlSubmit]);

  return (
    <div className="url-input-container">
      <form onSubmit={handleSubmit} className="url-input-form">
        <input
          type="url"
          value={url}
          onChange={handleUrlChange}
          placeholder="Paste YouTube URL here..."
          className="url-input"
          disabled={isSubmitting}
        />
        <button
          type="submit"
          disabled={isSubmitting || !url.trim()}
          className="submit-button"
        >
          {isSubmitting ? 'Adding...' : 'Download'}
        </button>
      </form>
      
      {message && (
        <div className={`status-message status-${message.type}`}>
          {message.text}
        </div>
      )}
    </div>
  );
};

export default UrlInput;