'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getJob, JobState, retryJob } from '@/lib/api';
import JobProgress from '@/components/JobProgress';
import MetadataConfirmation from '@/components/MetadataConfirmation';

export default function JobPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [job, setJob] = useState<JobState | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const next = await getJob(params.id);
      setJob(next);
      if (next.status === 'completed') router.replace(`/jobs/${params.id}/insight`);
    } catch (err: any) {
      setError(err.message || '无法读取分析任务');
    }
  }, [params.id, router]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 1800);
    return () => clearInterval(timer);
  }, [load]);

  if (error) return <div className="state-card"><h2>任务读取失败</h2><p>{error}</p></div>;
  if (!job) return <JobProgress stage="resolving" message="正在建立广告档案" />;
  if (job.status === 'needs_confirmation') return <MetadataConfirmation job={job} onResume={load} />;
  if (job.status === 'failed') {
    return (
      <div className="state-card danger">
        <p className="eyebrow">PROCESS INTERRUPTED</p>
        <h2>这一阶段没有跑通</h2>
        <p>{job.error_message || '发生未知错误'}</p>
        <button onClick={async () => { await retryJob(job.id); await load(); }}>从失败处重试</button>
      </div>
    );
  }
  return <JobProgress stage={job.stage} message={job.progress_message} />;
}
