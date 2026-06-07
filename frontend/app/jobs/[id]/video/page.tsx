'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getJob, getVideoStatus, generateVideo, videoDownloadUrl, JobState, VideoStatusResponse } from '@/lib/api';

const PIPELINE_STAGES = [
  { key: 'storyboard', label: '分镜脚本', line1: 'Agnes AI 分析数据', line2: '生成 7 场景分镜' },
  { key: 'visuals', label: '视觉素材', line1: 'AI 插图 + 雷达图', line2: '+ 文字卡片' },
  { key: 'audio', label: '配音生成', line1: 'Edge TTS 旁白', line2: '+ Pixabay 背景音乐' },
  { key: 'render', label: '视频合成', line1: 'MoviePy Ken Burns', line2: '+ 字幕 + 音轨混合' },
];

const STAGE_INDEX: Record<string, number> = {
  storyboard: 0,
  visuals: 1,
  audio: 2,
  render: 3,
};

export default function VideoPage() {
  const params = useParams();
  const id = params.id as string;

  const [job, setJob] = useState<JobState | null>(null);
  const [video, setVideo] = useState<VideoStatusResponse | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const loadVideoStatus = useCallback(async () => {
    try {
      const data = await getVideoStatus(id);
      setVideo(data);
      return data;
    } catch {
      return null;
    }
  }, [id]);

  useEffect(() => {
    getJob(id).then(setJob).catch(() => {});
    loadVideoStatus();
  }, [id, loadVideoStatus]);

  // Poll during generation
  useEffect(() => {
    if (!video || video.status !== 'generating') return;
    const timer = setInterval(async () => {
      const data = await loadVideoStatus();
      if (data && data.status !== 'generating') {
        setGenerating(false);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [video?.status, loadVideoStatus]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      await generateVideo(id);
      setVideo({ status: 'generating', video_url: '' });
    } catch (e: any) {
      setError(e.message || '生成失败');
      setGenerating(false);
    }
  };

  if (!job) {
    return (
      <div className="site-main">
        <div className="state-card"><p>加载中…</p></div>
      </div>
    );
  }

  const currentStage = video?.stage || '';
  const currentStageIdx = STAGE_INDEX[currentStage] ?? -1;
  const isGenerating = video?.status === 'generating' || generating;
  const isCompleted = video?.status === 'completed';
  const isFailed = video?.status === 'failed';
  const hasStarted = video?.status === 'generating' || video?.status === 'completed' || video?.status === 'failed';

  return (
    <div className="site-main">
      {/* Header */}
      <header className="dossier-head">
        <div>
          <p className="eyebrow">VIDEO / PRODUCTION PIPELINE</p>
          <h1>{job.brand_name}<em>{job.product_name} · 45s 横屏解说</em></h1>
        </div>
        <Link href={`/jobs/${id}/insight`} style={{ color: 'var(--red)', fontSize: 12 }}>
          返回分析报告 →
        </Link>
      </header>

      {/* Pipeline stages — like progress-sheet */}
      <div className="progress-sheet" style={{ marginTop: 38 }}>
        <p className="eyebrow">PIPELINE STAGES</p>
        <h2>视频生产管线</h2>

        <ol>
          {PIPELINE_STAGES.map((stage, idx) => {
            let state: 'done' | 'active' | 'pending' = 'pending';
            if (isCompleted) {
              state = 'done';
            } else if (isGenerating) {
              if (idx < currentStageIdx) state = 'done';
              else if (idx === currentStageIdx) state = 'active';
            } else if (isFailed && idx <= currentStageIdx && currentStageIdx >= 0) {
              if (idx < currentStageIdx) state = 'done';
              else if (idx === currentStageIdx) state = 'active';
            }

            return (
              <li key={stage.key} className={state === 'active' ? 'active' : state === 'done' ? 'done' : ''}>
                <span>{String(idx + 1).padStart(2, '0')}</span>
                <b>{stage.label}</b>
                <i style={{ textAlign: 'right' }}>
                  {state === 'done' ? '✓' : state === 'active' ? '···' : ''}
                </i>
              </li>
            );
          })}
        </ol>

        {/* Progress bar */}
        {hasStarted && (
          <div style={{ marginTop: 28, borderTop: '1px solid var(--line)', paddingTop: 22 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--muted)' }}>
              <span>{video?.progress_message || '准备中…'}</span>
              <span>{isCompleted ? 100 : video?.percent ?? 0}%</span>
            </div>
            <div style={{ height: 3, background: 'var(--line)' }}>
              <div style={{
                height: '100%',
                width: `${isCompleted ? 100 : video?.percent ?? 0}%`,
                background: isFailed ? 'var(--red)' : isCompleted ? 'var(--green)' : 'var(--red)',
                transition: 'width .7s ease-out',
              }} />
            </div>
          </div>
        )}
      </div>

      {/* Action area */}
      <div className="state-card" style={{ textAlign: 'center', marginTop: 28 }}>
        {isCompleted && (
          <>
            <p className="eyebrow">RENDER COMPLETE</p>
            <h2>视频生成完成</h2>
            <p>45 秒横屏解说视频已就绪，可下载或直接发布到平台。</p>
            <a
              href={videoDownloadUrl(id)}
              download
              className="report-action primary"
              style={{ display: 'inline-flex', marginTop: 16, gap: 8, fontSize: 12, padding: '12px 24px' }}
            >
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ marginRight: 4 }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              下载 MP4
            </a>
          </>
        )}

        {isFailed && (
          <>
            <p className="eyebrow" style={{ color: 'var(--red)' }}>PIPELINE FAILED</p>
            <h2>生成失败</h2>
            <p style={{ color: 'var(--red-dark)' }}>{video?.error || '发生未知错误'}</p>
            <p style={{ color: 'var(--muted)', fontSize: 12 }}>
              可能原因：API Key 未配置、网络异常、资源生成失败
            </p>
            <button
              onClick={handleGenerate}
              style={{ marginTop: 16, border: 0, background: 'var(--red)', color: 'white', padding: '12px 22px', fontSize: 13, fontWeight: 700 }}
            >
              重新生成
            </button>
          </>
        )}

        {isGenerating && (
          <>
            <p className="eyebrow">RENDERING IN PROGRESS</p>
            <h2>正在生成视频</h2>
            <p>预计需要 2–3 分钟，请耐心等待…</p>
            <div style={{
              display: 'inline-block',
              marginTop: 16,
              width: 20,
              height: 20,
              border: '2px solid var(--red)',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </>
        )}

        {!hasStarted && (
          <>
            <p className="eyebrow">VIDEO PRODUCTION</p>
            <h2>生成分析视频</h2>
            <p>
              将分析结果自动制成 45 秒横屏解说视频
              <br />
              <span style={{ color: 'var(--muted)', fontSize: 13 }}>
                AI 插图 + 雷达图 + 文字卡片 → 自动配音 → MoviePy 合成
              </span>
            </p>
            {error && <p style={{ color: 'var(--red-dark)', fontSize: 13, marginTop: 12 }}>{error}</p>}
            <button
              onClick={handleGenerate}
              disabled={generating}
              style={{ marginTop: 20, border: 0, background: 'var(--red)', color: 'white', padding: '14px 28px', fontSize: 14, fontWeight: 700, opacity: generating ? 0.45 : 1 }}
            >
              开始生成
            </button>
          </>
        )}
      </div>

      {/* Back link */}
      <div style={{ textAlign: 'center', marginTop: 32 }}>
        <Link
          href={`/jobs/${id}/insight`}
          style={{ color: 'var(--muted)', fontSize: 12, fontFamily: 'var(--mono)', letterSpacing: '.08em' }}
        >
          返回洞察报告
        </Link>
      </div>
    </div>
  );
}
