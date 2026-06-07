'use client';

import { useEffect, useState } from 'react';
import { getJob, JobState, generateVideo, getVideoStatus, videoDownloadUrl } from '@/lib/api';
import ResultNav from './ResultNav';
import CopyBlock from './CopyBlock';
import MarkdownPreview from './MarkdownPreview';
import ScoreCard from './ScoreCard';

export default function PublicationWorkspace({
  id,
  mode,
}: {
  id: string;
  mode: 'insight' | 'douyin' | 'xiaohongshu';
}) {
  const [job, setJob] = useState<JobState | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getJob(id).then(setJob).catch((err) => setError(err.message));
  }, [id]);

  if (error) return <div className="state-card danger"><h2>成果读取失败</h2><p>{error}</p></div>;
  if (!job) return <div className="state-card"><p>正在整理稿件…</p></div>;
  if (job.status !== 'completed') return <div className="state-card"><a href={`/jobs/${id}`}>返回分析进度</a></div>;

  const publishing = job.publishing || {};
  const meta = job.analysis?.analysis_meta || {};
  const audit = job.analysis?.quality_audit || {};
  const evidenceCount = meta.evidence_count ?? job.analysis?.material_understanding?.evidence_ledger?.length ?? 0;
  const trustScore = audit.trust_score ?? meta.trust_score ?? 0;
  const verdict = audit.verdict ?? meta.audit_verdict ?? 'review';
  const verdictLabel: Record<string, string> = {
    pass: '证据审查通过',
    review: '建议人工复核',
    reject: '不建议直接发布',
  };
  const sourceLabel: Record<string, string> = {
    video: '完整视频',
    frames: '关键帧',
    frames_fallback: '豆包失败 · 关键帧降级',
    text: '文本',
    text_fallback: '豆包失败 · 文本降级',
  };
  const header = (
    <header className="dossier-head">
      <div>
        <p className="eyebrow">{job.source_platform || 'VIDEO'} / CREATIVE DOSSIER</p>
        <h1>{job.brand_name}<em>{job.product_name}</em></h1>
      </div>
      <a href={job.source_url} target="_blank" rel="noreferrer">查看原始素材 ↗</a>
    </header>
  );

  return (
    <div className="result-workspace">
      {header}
      <ResultNav id={id} active={mode} />
      {mode === 'insight' && (
        <main className="manuscript">
          <section className={`trust-ledger verdict-${verdict}`}>
            <div className="trust-score">
              <span>TRUST SCORE</span>
              <strong>{trustScore}</strong>
              <small>/ 100</small>
            </div>
            <div className="trust-fact">
              <span>审查结论</span>
              <strong>{verdictLabel[verdict] || '建议人工复核'}</strong>
              <small>{(audit.unsupported_claims || []).length} 条未支持结论</small>
            </div>
            <div className="trust-fact">
              <span>证据覆盖</span>
              <strong>{evidenceCount} 条</strong>
              <small>带时间戳的事实账本</small>
            </div>
            <div className="trust-fact model-proof">
              <span>视频理解</span>
              <strong>{meta.video_model || '未记录'}</strong>
              <small>{sourceLabel[meta.source_mode] || meta.source_mode || '未知模式'}</small>
            </div>
          </section>
          <ScoreCard data={job.analysis?.scoring || null} />
          <MarkdownPreview id={id} content={job.analysis?.final_note?.markdown_content || '暂无洞察正文'} />
          <VideoSection adId={id} initialStatus={job.video_status} />
        </main>
      )}
      {mode === 'douyin' && (
        <main className="publication-grid">
          <section className="publication-intro">
            <p className="eyebrow">DOUYIN / READY TO PUBLISH</p>
            <h2>抖音发布包</h2>
            <p>图文稿与口播稿分开编辑，可以直接复制，也可以保留观点后再加个人表达。</p>
          </section>
          <CopyBlock label="图文标题" content={publishing.douyin_article?.title || ''} />
          <CopyBlock label="图文正文" content={[
            publishing.douyin_article?.hook,
            publishing.douyin_article?.body,
            publishing.douyin_article?.cta,
            (publishing.douyin_article?.hashtags || []).join(' '),
          ].filter(Boolean).join('\n\n')} />
          <CopyBlock label={`口播稿 · ${publishing.douyin_script?.duration_seconds || 75} 秒`} content={publishing.douyin_script?.full_script || ''} />
        </main>
      )}
      {mode === 'xiaohongshu' && (
        <main className="publication-grid">
          <section className="publication-intro">
            <p className="eyebrow">XIAOHONGSHU / SECONDARY EDIT</p>
            <h2>小红书适配稿</h2>
            <p>保留专业判断，压缩段落，并提供多标题与图片卡片结构。</p>
          </section>
          <CopyBlock label="标题备选" content={(publishing.xiaohongshu?.titles || []).join('\n')} />
          <CopyBlock label="发布正文" content={[
            publishing.xiaohongshu?.body,
            (publishing.xiaohongshu?.hashtags || []).join(' '),
          ].filter(Boolean).join('\n\n')} />
          <CopyBlock label="图片卡片建议" content={(publishing.xiaohongshu?.image_card_ideas || []).join('\n')} />
        </main>
      )}
    </div>
  );
}

function VideoSection({ adId, initialStatus }: { adId: string; initialStatus?: string }) {
  const [status, setStatus] = useState(initialStatus || '');
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (status === 'generating') {
      const timer = setInterval(async () => {
        try {
          const data = await getVideoStatus(adId);
          setStatus(data.status);
          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(timer);
          }
          if (data.status === 'failed' && data.error) {
            setMsg(data.error);
          }
        } catch { clearInterval(timer); }
      }, 3000);
      return () => clearInterval(timer);
    }
  }, [status, adId]);

  const handleGenerate = async () => {
    setGenerating(true);
    setMsg('');
    try {
      await generateVideo(adId);
      setStatus('generating');
    } catch (e: any) {
      setMsg(e.message || '生成失败');
    }
    setGenerating(false);
  };

  if (status === 'completed') {
    return (
      <div className="mt-8 p-5 border border-emerald-200 rounded-xl bg-emerald-50 text-center">
        <p className="text-sm font-semibold text-emerald-800 mb-3">分析视频已生成</p>
        <a
          href={videoDownloadUrl(adId)}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 transition-colors"
          download
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          下载视频 (MP4)
        </a>
      </div>
    );
  }

  return (
    <div className="mt-8 p-5 border border-stone-200 rounded-xl text-center">
      <p className="text-sm font-semibold text-stone-700 mb-2">生成分析视频</p>
      <p className="text-xs text-stone-500 mb-4">将分析结果自动制成 45 秒横屏解说视频</p>
      {msg && <p className="text-xs text-red-600 mb-2">{msg}</p>}
      <button
        className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-colors ${
          generating || status === 'generating'
            ? 'bg-stone-200 text-stone-500 cursor-not-allowed'
            : 'bg-stone-900 text-white hover:bg-stone-800'
        }`}
        disabled={generating || status === 'generating'}
        onClick={handleGenerate}
      >
        {status === 'generating' ? '生成中...' : generating ? '请求中...' : '生成分析视频'}
      </button>
    </div>
  );
}
