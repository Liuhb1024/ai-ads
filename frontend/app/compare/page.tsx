'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { listAds, compareAds, searchAds, AdSummary, CompareResponse, CompareSide } from '@/lib/api';

export default function ComparePage() {
  const [ads, setAds] = useState<AdSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState('');
  const [comparing, setComparing] = useState(false);

  const [searchA, setSearchA] = useState('');
  const [searchB, setSearchB] = useState('');
  const [selectedA, setSelectedA] = useState<AdSummary | null>(null);
  const [selectedB, setSelectedB] = useState<AdSummary | null>(null);
  const [showDropdownA, setShowDropdownA] = useState(false);
  const [showDropdownB, setShowDropdownB] = useState(false);
  const [dropdownAdsA, setDropdownAdsA] = useState<AdSummary[]>([]);
  const [dropdownAdsB, setDropdownAdsB] = useState<AdSummary[]>([]);
  const dropdownRefA = useRef<HTMLDivElement>(null);
  const dropdownRefB = useRef<HTMLDivElement>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    loadAds();
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRefA.current && !dropdownRefA.current.contains(e.target as Node)) setShowDropdownA(false);
      if (dropdownRefB.current && !dropdownRefB.current.contains(e.target as Node)) setShowDropdownB(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const loadAds = async () => {
    try {
      const data = await listAds(50);
      setAds(data.items);
    } catch {
      setError('加载广告列表失败');
    } finally {
      setLoading(false);
    }
  };

  const doSearch = async (q: string, setter: (items: AdSummary[]) => void) => {
    if (!q.trim()) {
      const completed = ads.filter((a) => a.status === 'completed');
      setter(completed.slice(0, 10));
      return;
    }
    try {
      const data = await searchAds(q, 10);
      setter(data.items);
    } catch {
      const ql = q.toLowerCase();
      setter(ads.filter((a) => a.status === 'completed' && [a.brand_name, a.product_name, a.industry].some((f) => f?.toLowerCase().includes(ql))).slice(0, 10));
    }
  };

  const handleSearchA = (q: string) => {
    setSearchA(q);
    setShowDropdownA(true);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => doSearch(q, setDropdownAdsA), 200);
  };

  const handleSearchB = (q: string) => {
    setSearchB(q);
    setShowDropdownB(true);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => doSearch(q, setDropdownAdsB), 200);
  };

  const selectA = (ad: AdSummary) => { setSelectedA(ad); setSearchA(`${ad.brand_name} — ${ad.product_name || '无产品'}`); setShowDropdownA(false); };
  const selectB = (ad: AdSummary) => { setSelectedB(ad); setSearchB(`${ad.brand_name} — ${ad.product_name || '无产品'}`); setShowDropdownB(false); };

  const handleCompare = async () => {
    if (!selectedA || !selectedB) return;
    setComparing(true);
    setError('');
    try {
      const res = await compareAds(selectedA.id, selectedB.id);
      setResult(res);
    } catch (err: any) {
      setError(err.message || '对比失败');
    } finally {
      setComparing(false);
    }
  };

  const winnerLabel = (id: string) => {
    if (!result) return null;
    if (result.predicted_winner === 'tie') return null;
    if (result.predicted_winner === 'A' && result.ad_a.ad_id === id) return '预测优势方';
    if (result.predicted_winner === 'B' && result.ad_b.ad_id === id) return '预测优势方';
    return null;
  };

  const confidenceCn: Record<string, string> = { high: '高置信度', medium: '中等置信度', low: '低置信度' };

  const sideCard = (side: CompareSide, label: string) => (
    <div className={`border rounded-xl p-5 space-y-3 ${winnerLabel(side.ad_id) ? 'border-emerald-400 bg-emerald-50' : 'border-stone-200'}`}>
      {winnerLabel(side.ad_id) && <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">{winnerLabel(side.ad_id)}</span>}
      <div className="text-lg font-semibold text-stone-800">{side.brand_name}</div>
      {side.product_name && <div className="text-sm text-stone-500">{side.product_name}</div>}
      <div className="flex gap-2 text-xs text-stone-400">{side.industry && <span>{side.industry}</span>}{side.platform && <span>{side.platform}</span>}</div>
      <div className="flex items-center gap-3">
        <div className="text-3xl font-bold text-stone-900">{side.overall_score}</div>
        <span className="text-xs text-stone-400">{side.tier}</span>
      </div>
      {side.strengths.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-stone-500 mb-1">优势</div>
          {side.strengths.map((s, i) => <div key={i} className="text-xs text-stone-600">+ {s}</div>)}
        </div>
      )}
      {side.weaknesses.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-stone-500 mb-1 mt-2">劣势</div>
          {side.weaknesses.map((w, i) => <div key={i} className="text-xs text-stone-500">- {w}</div>)}
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900">创意 A/B 对比</h1>
        <p className="text-sm text-stone-500 mt-1">选择两条已完成分析的广告，AI 将进行多维度对比并预测优势方</p>
      </div>

      {loading ? (
        <div className="text-stone-400 text-sm">加载中…</div>
      ) : (
        <>
          {/* Selection */}
          <div className="grid grid-cols-2 gap-6">
            <div ref={dropdownRefA} className="relative space-y-1">
              <label className="text-xs font-semibold text-stone-500">广告 A</label>
              <input
                type="text" className="w-full border border-stone-300 rounded-lg px-3 py-2 text-sm"
                placeholder="搜索品牌或产品名…" value={searchA} onChange={(e) => handleSearchA(e.target.value)}
                onFocus={() => doSearch(searchA, setDropdownAdsA)}
              />
              {showDropdownA && dropdownAdsA.length > 0 && (
                <div className="absolute z-10 w-full bg-white border border-stone-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {dropdownAdsA.map((ad) => (
                    <button key={ad.id} className="w-full text-left px-3 py-2 hover:bg-stone-50 text-sm" onClick={() => selectA(ad)}>
                      {ad.brand_name} — {ad.product_name || '无产品'} <span className="text-stone-400 text-xs">{ad.industry}</span>
                    </button>
                  ))}
                </div>
              )}
              {selectedA && <div className="text-xs text-emerald-600">已选：{selectedA.brand_name} — {selectedA.product_name || '无产品'}</div>}
            </div>
            <div ref={dropdownRefB} className="relative space-y-1">
              <label className="text-xs font-semibold text-stone-500">广告 B</label>
              <input
                type="text" className="w-full border border-stone-300 rounded-lg px-3 py-2 text-sm"
                placeholder="搜索品牌或产品名…" value={searchB} onChange={(e) => handleSearchB(e.target.value)}
                onFocus={() => doSearch(searchB, setDropdownAdsB)}
              />
              {showDropdownB && dropdownAdsB.length > 0 && (
                <div className="absolute z-10 w-full bg-white border border-stone-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {dropdownAdsB.map((ad) => (
                    <button key={ad.id} className="w-full text-left px-3 py-2 hover:bg-stone-50 text-sm" onClick={() => selectB(ad)}>
                      {ad.brand_name} — {ad.product_name || '无产品'} <span className="text-stone-400 text-xs">{ad.industry}</span>
                    </button>
                  ))}
                </div>
              )}
              {selectedB && <div className="text-xs text-emerald-600">已选：{selectedB.brand_name} — {selectedB.product_name || '无产品'}</div>}
            </div>
          </div>

          <button
            className="px-6 py-2.5 bg-stone-900 text-white rounded-lg text-sm disabled:opacity-30"
            disabled={!selectedA || !selectedB || comparing}
            onClick={handleCompare}
          >
            {comparing ? '分析中…' : '开始对比'}
          </button>

          {error && <div className="text-red-600 text-sm">{error}</div>}

          {/* Results */}
          {result && (
            <div className="space-y-6">
              {result.predicted_winner !== 'tie' && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
                  <span className="text-sm font-semibold text-emerald-800">
                    预测优势方：{result.predicted_winner === 'A' ? result.ad_a.brand_name : result.ad_b.brand_name}
                  </span>
                  <span className="text-xs text-emerald-600 ml-2">（{confidenceCn[result.confidence] || result.confidence}）</span>
                </div>
              )}
              {result.predicted_winner === 'tie' && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <span className="text-sm font-semibold text-amber-800">两条广告竞争力接近</span>
                  <span className="text-xs text-amber-600 ml-2">（{confidenceCn[result.confidence] || result.confidence}）</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-6">
                {sideCard(result.ad_a, 'A')}
                {sideCard(result.ad_b, 'B')}
              </div>

              {result.key_differences.length > 0 && (
                <div className="bg-stone-50 border border-stone-200 rounded-xl p-5 space-y-2">
                  <div className="text-sm font-semibold text-stone-700">关键差异</div>
                  {result.key_differences.map((d, i) => (
                    <div key={i} className="text-sm text-stone-600 flex gap-2">
                      <span className="text-stone-400">{i + 1}.</span> {d}
                    </div>
                  ))}
                </div>
              )}

              {result.hook_comparison && (
                <div className="border border-stone-200 rounded-xl p-5 space-y-1">
                  <div className="text-sm font-semibold text-stone-700">钩子对比</div>
                  <div className="text-sm text-stone-600">{result.hook_comparison}</div>
                </div>
              )}

              {result.audience_comparison && (
                <div className="border border-stone-200 rounded-xl p-5 space-y-1">
                  <div className="text-sm font-semibold text-stone-700">人群匹配对比</div>
                  <div className="text-sm text-stone-600">{result.audience_comparison}</div>
                </div>
              )}

              {result.trust_comparison && (
                <div className="border border-stone-200 rounded-xl p-5 space-y-1">
                  <div className="text-sm font-semibold text-stone-700">信任机制对比</div>
                  <div className="text-sm text-stone-600">{result.trust_comparison}</div>
                </div>
              )}

              {result.analysis_markdown && (
                <div className="border border-stone-200 rounded-xl p-5">
                  <div className="text-sm font-semibold text-stone-700 mb-3">完整分析</div>
                  <div className="prose prose-sm text-stone-600 whitespace-pre-wrap">{result.analysis_markdown}</div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
