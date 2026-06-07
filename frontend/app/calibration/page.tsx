'use client';

import { useEffect, useState } from 'react';
import { listAds, getAd, submitExpertScore, listExpertScores, AdSummary, AdDetail } from '@/lib/api';

const DIMENSIONS = [
  { key: 'overall_score', label: '综合评分', range: [0, 100] },
  { key: 'hook_score', label: '钩子', range: [1, 5] },
  { key: 'messaging_score', label: '信息传递', range: [1, 5] },
  { key: 'conversion_score', label: '转化设计', range: [1, 5] },
  { key: 'emotion_score', label: '情绪调动', range: [1, 5] },
  { key: 'trust_score', label: '信任建立', range: [1, 5] },
  { key: 'production_score', label: '制作水准', range: [1, 5] },
  { key: 'innovation_score', label: '创新性', range: [1, 5] },
];

export default function CalibrationPage() {
  const [ads, setAds] = useState<AdSummary[]>([]);
  const [expertId, setExpertId] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const [aiScores, setAiScores] = useState<Record<string, number> | null>(null);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    listAds(50).then((d) => setAds(d.items.filter((a) => a.status === 'completed'))).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const eid = localStorage.getItem('calibration_expert_id') || '';
    setExpertId(eid);
    if (eid) loadProgress(eid);
  }, []);

  const loadProgress = async (eid: string) => {
    try {
      const data = await listExpertScores(eid);
      setSubmitted(data.count);
    } catch {}
  };

  const handleSelect = async (id: string) => {
    setSelectedId(id);
    setMsg('');
    try {
      const ad = await getAd(id) as AdDetail;
      const scoring = (ad.analysis as any)?.scoring?.scoring || {};
      const ai: Record<string, number> = {};
      if (scoring.overall_score) ai.overall_score = scoring.overall_score;
      for (const dim of DIMENSIONS) {
        if (dim.key === 'overall_score') continue;
        const catKey = dim.key.replace('_score', '');
        const cat = scoring[catKey];
        if (cat) {
          const vals = Object.values(cat).filter((v) => typeof v === 'number') as number[];
          if (vals.length) ai[dim.key] = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
        }
      }
      setAiScores(ai);
      setScores(Object.fromEntries(DIMENSIONS.map((d) => [d.key, d.range[1] === 100 ? ai[d.key] || 50 : ai[d.key] || 3])));
    } catch { setMsg('加载AI评分失败'); }
  };

  const handleSubmit = async () => {
    if (!expertId.trim() || !selectedId) { setMsg('请填写专家ID并选择广告'); return; }
    localStorage.setItem('calibration_expert_id', expertId.trim());
    try {
      await submitExpertScore({
        ad_id: selectedId, expert_id: expertId.trim(),
        overall_score: scores.overall_score || 50,
        hook_score: scores.hook_score || 3,
        messaging_score: scores.messaging_score || 3,
        conversion_score: scores.conversion_score || 3,
        emotion_score: scores.emotion_score || 3,
        trust_score: scores.trust_score || 3,
        production_score: scores.production_score || 3,
        innovation_score: scores.innovation_score || 3,
        notes: notes || undefined,
      });
      setMsg('提交成功');
      setSubmitted((n) => n + 1);
      setSelectedId('');
      setAiScores(null);
      setNotes('');
    } catch (err: any) { setMsg(err.message); }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900">创意评分校准</h1>
        <p className="text-sm text-stone-500 mt-1">为广告打分，评估 AI 评分与人类判断的一致性</p>
      </div>

      {loading ? <div className="text-stone-400 text-sm">加载中…</div> : (
        <div className="grid grid-cols-3 gap-6">
          {/* Ad list */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-stone-500">选择广告 ({ads.length} 条已完成)</div>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {ads.map((ad) => (
                <button key={ad.id}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${selectedId === ad.id ? 'bg-stone-900 text-white' : 'bg-stone-100 hover:bg-stone-200 text-stone-700'}`}
                  onClick={() => handleSelect(ad.id)}
                >
                  {ad.brand_name} — {ad.product_name || '无产品'}
                  <span className="text-xs opacity-60 ml-1">{ad.industry}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Score form */}
          <div className="col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <input type="text" className="border border-stone-300 rounded-lg px-3 py-2 text-sm w-40" placeholder="专家ID (如 A01)"
                value={expertId} onChange={(e) => setExpertId(e.target.value)} />
              <span className="text-xs text-stone-400">已评分: {submitted} 条</span>
            </div>

            {!selectedId && <div className="text-stone-400 text-sm py-8">← 选择一条广告开始评分</div>}

            {selectedId && aiScores && (
              <div className="space-y-4">
                {DIMENSIONS.map((dim) => (
                  <div key={dim.key} className="flex items-center gap-4">
                    <label className="w-24 text-sm font-medium text-stone-600">{dim.label}</label>
                    <input type="range" min={dim.range[0]} max={dim.range[1]} value={scores[dim.key] || dim.range[0]}
                      onChange={(e) => setScores((s) => ({ ...s, [dim.key]: Number(e.target.value) }))} className="flex-1" />
                    <span className="w-8 text-right text-sm font-bold text-stone-800">{scores[dim.key]}</span>
                    <span className="w-8 text-right text-xs text-stone-400">AI: {aiScores[dim.key] ?? '-'}</span>
                  </div>
                ))}
                <textarea className="w-full border border-stone-300 rounded-lg px-3 py-2 text-sm" rows={2}
                  placeholder="评分备注 (可选)" value={notes} onChange={(e) => setNotes(e.target.value)} />
                <button className="px-6 py-2.5 bg-stone-900 text-white rounded-lg text-sm" onClick={handleSubmit}>
                  提交评分
                </button>
                {msg && <div className={`text-sm ${msg.includes('成功') ? 'text-emerald-600' : 'text-red-600'}`}>{msg}</div>}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
