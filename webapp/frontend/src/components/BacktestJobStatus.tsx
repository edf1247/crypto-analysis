import { useState, useEffect } from 'react';
import { fetchBacktestJobs, pollJobStatus } from '../services/api';
import type { BacktestJob } from '../services/api';

interface BacktestJobStatusProps {
  refreshInterval?: number; // milliseconds between refreshes
  showCompleted?: boolean; // whether to show completed/failed jobs
}

const BacktestJobStatus = ({ refreshInterval = 5000, showCompleted = false }: BacktestJobStatusProps) => {
  const [jobs, setJobs] = useState<BacktestJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pollingJobs, setPollingJobs] = useState<Set<number>>(new Set());

  const loadJobs = async () => {
    try {
      setLoading(true);
      const allJobs = await fetchBacktestJobs();
      // Filter jobs based on showCompleted
      const filteredJobs = showCompleted
        ? allJobs
        : allJobs.filter(job => job.status === 'pending' || job.status === 'running');
      setJobs(filteredJobs);
      setError(null);
    } catch (err) {
      setError('Failed to load backtest jobs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadJobs();
  }, [showCompleted]);

  // Set up interval refresh for active jobs
  useEffect(() => {
    const interval = setInterval(() => {
      // Only refresh if there are pending/running jobs
      const activeJobs = jobs.filter(job => job.status === 'pending' || job.status === 'running');
      if (activeJobs.length > 0) {
        loadJobs();
      }
    }, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, jobs]);

  // Start polling for jobs that are pending/running
  useEffect(() => {
    const pendingRunningJobs = jobs.filter(job => job.status === 'pending' || job.status === 'running');
    const newPollingSet = new Set(pollingJobs);
    let changed = false;

    pendingRunningJobs.forEach(job => {
      if (!pollingJobs.has(job.id)) {
        newPollingSet.add(job.id);
        changed = true;
        // Start polling for this job
        pollJobStatus(job.id).then(updatedJob => {
          // Update the job in the list
          setJobs(prev => prev.map(j => j.id === updatedJob.id ? updatedJob : j));
          // Remove from polling set once completed/failed
          if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
            setPollingJobs(prev => {
              const newSet = new Set(prev);
              newSet.delete(updatedJob.id);
              return newSet;
            });
          }
        }).catch(err => {
          console.error(`Polling failed for job ${job.id}`, err);
        });
      }
    });

    // Remove jobs that are no longer pending/running from polling set
    pollingJobs.forEach(jobId => {
      const job = jobs.find(j => j.id === jobId);
      if (!job || (job.status !== 'pending' && job.status !== 'running')) {
        newPollingSet.delete(jobId);
        changed = true;
      }
    });

    if (changed) {
      setPollingJobs(newPollingSet);
    }
  }, [jobs]);

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'orange';
      case 'running': return 'blue';
      case 'completed': return 'green';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };

  if (loading && jobs.length === 0) return <div>Loading jobs...</div>;
  if (error) return <div className="error">{error}</div>;

  const activeJobs = jobs.filter(job => job.status === 'pending' || job.status === 'running');
  const completedJobs = jobs.filter(job => job.status === 'completed' || job.status === 'failed');

  return (
    <div className="backtest-job-status">
      <h2>Backtest Jobs</h2>

      {activeJobs.length > 0 && (
        <div className="active-jobs">
          <h3>Active Jobs ({activeJobs.length})</h3>
          <table className="jobs-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Strategy</th>
                <th>Symbol</th>
                <th>Interval</th>
                <th>Status</th>
                <th>Created</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {activeJobs.map(job => (
                <tr key={job.id}>
                  <td>{job.id}</td>
                  <td>{job.strategy_name}</td>
                  <td>{job.symbol}</td>
                  <td>{job.interval}</td>
                  <td>
                    <span style={{ color: getStatusColor(job.status), fontWeight: 'bold' }}>
                      {job.status.toUpperCase()}
                    </span>
                  </td>
                  <td>{formatDate(job.created_at)}</td>
                  <td>{formatDate(job.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCompleted && completedJobs.length > 0 && (
        <div className="completed-jobs">
          <h3>Completed/Failed Jobs ({completedJobs.length})</h3>
          <table className="jobs-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Strategy</th>
                <th>Symbol</th>
                <th>Status</th>
                <th>Result</th>
                <th>Created</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {completedJobs.map(job => (
                <tr key={job.id}>
                  <td>{job.id}</td>
                  <td>{job.strategy_name}</td>
                  <td>{job.symbol}</td>
                  <td>
                    <span style={{ color: getStatusColor(job.status), fontWeight: 'bold' }}>
                      {job.status.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {job.status === 'completed' ? (
                      <a href={`/backtest-runs/${job.backtest_run_id}`} target="_blank" rel="noopener noreferrer">
                        View Results
                      </a>
                    ) : '-'}
                  </td>
                  <td>{formatDate(job.created_at)}</td>
                  <td>{job.error_message || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {jobs.length === 0 && (
        <p>No backtest jobs found.</p>
      )}
    </div>
  );
};

export default BacktestJobStatus;