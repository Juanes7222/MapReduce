import { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function JobForm({ onJobCreated }) {
  const [text, setText] = useState('');
  const [strategy, setStrategy] = useState('round_robin');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      toast.error('Please enter some text');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await axios.post(`${API}/jobs`, {
        text: text,
        balancing_strategy: strategy
      });
      
      toast.success(`Job created: ${response.data.job_id}`);
      setText('');
      onJobCreated();
    } catch (error) {
      toast.error('Failed to create job');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setText(event.target.result);
      toast.success('File loaded');
    };
    reader.readAsText(file);
  };

  const loadSampleText = () => {
    const sample = `The quick brown fox jumps over the lazy dog. The dog was really lazy and did not chase the fox. 
    The fox was very quick and clever. It jumped high over the dog. The brown fox is a common sight in many forests. 
    Dogs are loyal animals and they love to play. The lazy dog finally got up and started to run. 
    However, the quick fox was already gone. This story teaches us about the importance of being quick and alert. 
    The fox and the dog represent different personalities. Some people are like the quick fox, always ready to act. 
    Others are like the lazy dog, preferring to rest. Both have their place in the world.`.repeat(5);
    setText(sample);
    toast.success('Sample text loaded');
  };

  return (
    <div className="job-form-container" data-testid="job-form">
      <div className="card">
        <h2 className="card-title">Create MapReduce Job</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="text-input">Text Input</label>
            <textarea
              id="text-input"
              data-testid="text-input"
              className="form-textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter text to analyze or upload a file..."
              rows={8}
            />
            <div className="text-info">
              {text.length} characters
            </div>
          </div>

          <div className="form-actions">
            <label className="file-upload-btn" data-testid="file-upload-label">
              <input
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                data-testid="file-upload-input"
              />
              Upload .txt
            </label>
            <button
              type="button"
              onClick={loadSampleText}
              className="secondary-btn"
              data-testid="load-sample-btn"
            >
              Load Sample
            </button>
          </div>

          <div className="form-group">
            <label htmlFor="strategy-select">Balancing Strategy</label>
            <select
              id="strategy-select"
              data-testid="strategy-select"
              className="form-select"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="round_robin">Round Robin</option>
              <option value="least_loaded">Least Loaded</option>
            </select>
          </div>

          <button
            type="submit"
            className="submit-btn"
            disabled={isSubmitting}
            data-testid="submit-job-btn"
          >
            {isSubmitting ? 'Creating...' : 'Start Job'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default JobForm;
