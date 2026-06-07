'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getJob, getVideoStatus, generateVideo, videoDownloadUrl, JobState, VideoStatusResponse } from '@/lib/api';

interface StageInfo {
  key: string;
  label: string;
  headline: string;
  details: string[];
  input: string;
  output: string;
}

const PIPELINE_STAGES: StageInfo[] = [
  {
    key: 'storyboard',
    label: '分镜脚本',
    headline: 'Agnes AI 读取分析 JSON，生成 7 场景分镜',
    details: [
      '提取 scoring / ad_strategy / user_insight / final_note 关键字段',
      '按 钩子→策略→人群→创意→信任→评分→金句 节奏分配 45 秒',
      '每个场景输出: visual_prompt（生图提示词）+ narration（旁白） + overlay_text（大字标题）',
      '不提及品牌名，避免版权风险',
    ],
    input: 'analysis_json 全文',
    output: '7-scene storyboard JSON',
  },
  {
    key: 'visuals',
    label: '视觉素材',
    headline: '并行生成：AI 概念插图 + matplotlib 雷达图 + Pillow 文字卡片',
    details: [
      'Agnes Image 模型: 根据 visual_prompt 生成 1792×1024 概念插图（4-5 张）',
      'matplotlib: 从 scoring 数据绘制 7 维雷达图，暗色主题，透明背景',
      'Pillow: 渲染中文大字卡片，半透明叠加层，PingFang 字体',
      'API 失败时自动降级为文字卡片',
    ],
    input: 'storyboard.visual_prompt + analysis.scoring',
    output: 'PNG 图片集（7 张）',
  },
  {
    key: 'audio',
    label: '配音生成',
    headline: 'Edge TTS 旁白 + Pixabay 背景音乐，并行生成',
    details: [
      'Edge TTS: zh-CN-YunxiNeural（男声），逐场景生成 mp3 + 词级时间戳',
      'Pixabay API: 搜索 corporate / cinematic 风格 BGM，时长 ≥ 40s',
      'VTT 字幕解析: 提取每句起止时间，用于字幕同步',
      'TTS 失败自动切换 XiaoxiaoNeural 备用音色',
    ],
    input: 'storyboard.narration × 7',
    output: '7 个 mp3 + 字幕时间戳 + 1 个 BGM mp3',
  },
  {
    key: 'render',
    label: '视频合成',
    headline: 'MoviePy 合成: Ken Burns 动画 + 文字叠加 + 字幕同步 + 音轨混合',
    details: [
      'Ken Burns: 每张背景图缓慢缩放/平移，保持画面动感',
      '文字叠加: Pillow 渲染的中文 PNG 透明叠加（保证字体正确）',
      '字幕同步: 按词级时间戳逐词显示，底部居中',
      '音轨混合: TTS 旁白 100% + BGM 18% 音量',
      '场景间 cross-fade 0.4s 过渡',
      '输出: H.264 MP4, 1920×1080, 25fps, 5000kbps',
    ],
    input: 'images + audio + storyboard',
    output: 'video.mp4 (45s, ~28MB)',
  },
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

  useEffect(() => {
    if (!video || video.status !== 'generating') return;
    const timer = setInterval(async () => {
      const data = await loadVideoStatus();
      if (data && data.status !== 'generating') setGenerating(false);
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
  const hasStarted = isGenerating || isCompleted || isFailed;

  return (
    <div className="site-main">
      {/* Header */}
      <header className="dossier-head">
        <div>
          <p className="eyebrow">VIDEO PRODUCTION PIPELINE</p>
          <h1>{job.brand_name}<em>{job.product_name} · 45s 横屏解说</em></h1>
        </div>
        <Link href={`/jobs/${id}/insight`} style={{ color: 'var(--red)', fontSize: 12 }}>
          返回分析报告 ↗
        </Link>
      </header>

      {/* Pipeline stages — progress-sheet style */}
      <div className="progress-sheet" style={{ marginTop: 38 }}>
        <p className="eyebrow">PIPELINE STAGES</p>
        <h2>视频生产管线</h2>

        <ol>
          {PIPELINE_STAGES.map((stage, idx) => {
            let state: 'done' | 'active' | 'pending' = 'pending';
            if (isCompleted) state = 'done';
            else if (isGenerating) {
              if (idx < currentStageIdx) state = 'done';
              else if (idx === currentStageIdx) state = 'active';
            } else if (isFailed && currentStageIdx >= 0) {
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
            <div style={{
              display: 'flex', justifyContent: 'space-between', marginBottom: 8,
              fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--muted)',
            }}>
              <span>{isCompleted ? 'RENDER COMPLETE' : isFailed ? 'PIPELINE FAILED' : video?.progress_message || '准备中…'}</span>
              <span>{isCompleted ? 100 : Math.max(video?.percent ?? 0, hasStarted ? 1 : 0)}%</span>
            </div>
            <div style={{ height: 3, background: 'var(--line)' }}>
              <div style={{
                height: '100%',
                width: `${isCompleted ? 100 : isFailed ? Math.max((video?.percent ?? 0), currentStageIdx >= 0 ? (currentStageIdx + 1) * 25 : 5) : video?.percent ?? 0}%`,
                background: isFailed ? 'var(--red)' : isCompleted ? 'var(--green)' : 'var(--red)',
                transition: 'width .7s ease-out',
              }} />
            </div>
          </div>
        )}
      </div>

      {/* Stage detail cards */}
      <div style={{ marginTop: 28 }}>
        {PIPELINE_STAGES.map((stage, idx) => {
          let state: 'done' | 'active' | 'pending' = 'pending';
          if (isCompleted) state = 'done';
          else if (isGenerating) {
            if (idx < currentStageIdx) state = 'done';
            else if (idx === currentStageIdx) state = 'active';
          } else if (isFailed && currentStageIdx >= 0) {
            if (idx < currentStageIdx) state = 'done';
            else if (idx === currentStageIdx) state = 'active';
          }

          const borderColor = state === 'active' ? 'var(--red)' : state === 'done' ? 'var(--green)' : 'var(--line)';

          return (
            <div
              key={stage.key}
              style={{
                border: `1px solid ${borderColor}`,
                borderLeft: `4px solid ${borderColor}`,
                background: state === 'active' ? 'rgba(191,59,43,.04)' : 'var(--sheet)',
                padding: '22px 28px',
                marginBottom: 12,
                transition: 'border-color .5s, background .5s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 10 }}>
                <span style={{ color: 'var(--red)', font: '10px var(--mono)', letterSpacing: '.12em' }}>
                  {String(idx + 1).padStart(2, '0')}
                </span>
                <strong style={{ font: '500 20px var(--serif)' }}>{stage.label}</strong>
                {state === 'done' && <span style={{ color: 'var(--green)', fontSize: 12 }}>✓ 完成</span>}
                {state === 'active' && (
                  <span style={{ color: 'var(--red)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{
                      display: 'inline-block', width: 8, height: 8,
                      background: 'var(--red)', borderRadius: '50%',
                      animation: 'pulse 1.2s ease-in-out infinite',
                    }} />
                    执行中
                  </span>
                )}
              </div>

              <p style={{ font: '500 15px/1.6 var(--serif)', margin: '0 0 10px' }}>{stage.headline}</p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
                {stage.details.map((d, di) => (
                  <div key={di} style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                    <span style={{ color: 'var(--muted)', fontSize: 11, flexShrink: 0 }}>—</span>
                    <span style={{ color: 'var(--muted)', fontSize: 12, lineHeight: 1.7 }}>{d}</span>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', gap: 24, paddingTop: 10, borderTop: '1px solid var(--line)' }}>
                <div>
                  <span style={{ color: 'var(--muted)', font: '9px var(--mono)', letterSpacing: '.08em', textTransform: 'uppercase' }}>输入</span>
                  <span style={{ display: 'block', marginTop: 2, fontSize: 12, fontFamily: 'var(--mono)', color: 'var(--ink)' }}>{stage.input}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--muted)', font: '9px var(--mono)', letterSpacing: '.08em', textTransform: 'uppercase' }}>输出</span>
                  <span style={{ display: 'block', marginTop: 2, fontSize: 12, fontFamily: 'var(--mono)', color: 'var(--ink)' }}>{stage.output}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Action area */}
      <div className="state-card" style={{ textAlign: 'center', marginTop: 28 }}>
        {isCompleted && (
          <>
            <p className="eyebrow">RENDER COMPLETE</p>
            <h2>视频生成完成</h2>
            <p>45 秒横屏解说视频已就绪。</p>
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
              display: 'inline-block', marginTop: 16,
              width: 20, height: 20,
              border: '2px solid var(--red)', borderTopColor: 'transparent', borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } } @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }`}</style>
          </>
        )}

        {!hasStarted && (
          <>
            <p className="eyebrow">VIDEO PRODUCTION</p>
            <h2>制作分析视频</h2>
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
              style={{ marginTop: 20, border: 0, background: 'var(--red)', color: 'white', padding: '14px 28px', fontSize: 14, fontWeight: 700, opacity: generating ? .45 : 1 }}
            >
              开始生成
            </button>
          </>
        )}
      </div>

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
