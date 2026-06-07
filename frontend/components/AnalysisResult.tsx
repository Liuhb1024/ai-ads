'use client';

import { useState } from 'react';
import { analyzeAd, getAnalysis, exportMarkdownUrl } from '@/lib/api';
import MarkdownPreview from './MarkdownPreview';

interface Props {
  adId: string;
  initialStatus: string;
  initialAnalysis?: any;
}

export default function AnalysisResult({ adId, initialStatus, initialAnalysis }: Props) {
  const [status, setStatus] = useState(initialStatus);
  const [analysis, setAnalysis] = useState<any>(initialAnalysis || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await analyzeAd(adId);
      setStatus('completed');
      setAnalysis(result.result);
    } catch (err: any) {
      setError(err.message || '分析失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const url = await exportMarkdownUrl(adId);
      window.open(url, '_blank');
    } catch (err: any) {
      setError(err.message || '下载失败');
    }
  };

  const btnPrimary = "rounded-lg bg-stone-900 px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400";
  const btnSecondary = "rounded-lg border border-stone-200 bg-white px-4 py-2 text-xs text-stone-500 transition-colors hover:border-stone-300 hover:text-stone-700";

  if (status === 'pending') {
    return (
      <div className="py-16 text-center">
        <p className="mb-6 text-sm text-stone-500">
          尚未分析，点击下方按钮开始 AI 分析（当前为 Mock 模式）
        </p>
        <button onClick={handleAnalyze} disabled={loading} className={btnPrimary}>
          {loading ? '分析中...' : '开始分析'}
        </button>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>
    );
  }

  if (status === 'analyzing') {
    return (
      <div className="py-16 text-center">
        <p className="mb-4 text-sm text-stone-500">分析中，请稍候...</p>
        <div className="mx-auto mb-6 h-1.5 w-64 overflow-hidden rounded-full bg-stone-100">
          <div className="h-full w-2/3 animate-pulse rounded-full bg-stone-300" />
        </div>
        <button
          onClick={async () => {
            try {
              const data = await getAnalysis(adId);
              if (data.status === 'completed') {
                window.location.reload();
              }
            } catch {}
          }}
          className={btnSecondary}
        >
          刷新状态
        </button>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="py-16 text-center">
        <p className="mb-2 text-sm font-medium text-red-600">分析失败</p>
        {error && <p className="mb-6 text-sm text-red-500">{error}</p>}
        <button onClick={handleAnalyze} disabled={loading} className={btnPrimary}>
          重试分析
        </button>
      </div>
    );
  }

  const markdown = analysis?.final_note?.markdown_content || '';
  const takeaway = analysis?.final_note?.one_sentence_takeaway || '';

  return (
    <div>
      {takeaway && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50/50 px-5 py-4 text-sm text-amber-800">
          <span className="font-semibold">一句话洞察：</span>{takeaway}
        </div>
      )}

      <div className="mb-6 flex gap-3">
        <button onClick={handleDownload} className={btnPrimary}>
          下载 .md
        </button>
        {status === 'completed' && (
          <button onClick={handleAnalyze} disabled={loading} className={btnSecondary}>
            {loading ? '重新分析中...' : '重新分析'}
          </button>
        )}
        {error && <p className="self-center text-sm text-red-600">{error}</p>}
      </div>

      {markdown ? (
        <MarkdownPreview id={adId} content={markdown} />
      ) : (
        <p className="text-sm text-stone-400">未找到分析内容</p>
      )}
    </div>
  );
}
