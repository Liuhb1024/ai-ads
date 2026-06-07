'use client';

import { useEffect, useState } from 'react';
import { fetchCalibrationReport, CalibrationReport } from '@/lib/api';

export default function CalibrationReportPage() {
  const [report, setReport] = useState<CalibrationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCalibrationReport().then(setReport).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-stone-400 text-sm">加载中…</div>;
  if (error) return <div className="text-red-600 text-sm">{error}</div>;
  if (!report || report.n_ads === 0) return <div className="text-stone-500 text-sm">暂无校准数据，请先让专家完成评分</div>;

  const label = (rho: number | null, label: string) => {
    if (rho === null) return '数据不足';
    return `${label} (ρ=${rho.toFixed(3)})`;
  };

  const strengthColor = (label: string) => {
    if (label === '强相关') return 'text-emerald-600';
    if (label === '中等相关') return 'text-amber-600';
    if (label === '弱相关') return 'text-orange-500';
    return 'text-stone-400';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900">评分校准报告</h1>
        <p className="text-sm text-stone-500 mt-1">AI 评分与人类专家的一致性分析</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="border border-stone-200 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-stone-900">{report.n_ads}</div>
          <div className="text-xs text-stone-500 mt-1">广告数</div>
        </div>
        <div className="border border-stone-200 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-stone-900">{report.n_experts}</div>
          <div className="text-xs text-stone-500 mt-1">专家数</div>
        </div>
        <div className="border border-stone-200 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-stone-900">
            {report.overall_spearman_rho !== null ? report.overall_spearman_rho.toFixed(3) : '—'}
          </div>
          <div className="text-xs text-stone-500 mt-1">Spearman ρ</div>
        </div>
        <div className="border border-stone-200 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-stone-900">
            {report.tier_agreement !== null ? `${(report.tier_agreement * 100).toFixed(0)}%` : '—'}
          </div>
          <div className="text-xs text-stone-500 mt-1">等级一致率</div>
        </div>
      </div>

      {/* Per-dimension table */}
      <div className="border border-stone-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-stone-50 text-left">
              <th className="px-4 py-3 font-semibold text-stone-600">维度</th>
              <th className="px-4 py-3 font-semibold text-stone-600">Spearman ρ</th>
              <th className="px-4 py-3 font-semibold text-stone-600">p 值</th>
              <th className="px-4 py-3 font-semibold text-stone-600">相关性</th>
              <th className="px-4 py-3 font-semibold text-stone-600">样本数</th>
              <th className="px-4 py-3 font-semibold text-stone-600">AI 均值</th>
              <th className="px-4 py-3 font-semibold text-stone-600">专家均值</th>
            </tr>
          </thead>
          <tbody>
            {report.per_dimension.map((dim) => (
              <tr key={dim.dimension} className="border-t border-stone-100">
                <td className="px-4 py-2.5 font-medium text-stone-700">{dim.label}</td>
                <td className="px-4 py-2.5 font-mono">{dim.spearman_rho !== null ? dim.spearman_rho.toFixed(3) : '—'}</td>
                <td className="px-4 py-2.5 font-mono text-stone-500">{dim.p_value !== null ? dim.p_value.toFixed(3) : '—'}</td>
                <td className={`px-4 py-2.5 font-semibold ${strengthColor(dim.correlation_label)}`}>{dim.correlation_label}</td>
                <td className="px-4 py-2.5">{dim.n_pairs}</td>
                <td className="px-4 py-2.5 font-mono text-stone-500">{dim.ai_mean.toFixed(1)}</td>
                <td className="px-4 py-2.5 font-mono text-stone-500">{dim.expert_mean.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Expert reliability */}
      {Object.keys(report.expert_reliability).length > 0 && (
        <div className="border border-stone-200 rounded-xl p-5 space-y-2">
          <div className="text-sm font-semibold text-stone-700">专家间信度</div>
          {Object.entries(report.expert_reliability).map(([eid, rho]) => (
            <div key={eid} className="text-sm text-stone-600">
              {eid}: {rho !== null ? `ρ = ${rho.toFixed(3)}` : '数据不足'}
            </div>
          ))}
        </div>
      )}

      {/* Bar chart (simple CSS bars) */}
      <div className="border border-stone-200 rounded-xl p-5 space-y-3">
        <div className="text-sm font-semibold text-stone-700">各维度相关系数</div>
        <div className="space-y-2">
          {report.per_dimension.filter((d) => d.spearman_rho !== null).map((dim) => (
            <div key={dim.dimension} className="flex items-center gap-3">
              <span className="w-20 text-xs text-stone-600">{dim.label}</span>
              <div className="flex-1 bg-stone-100 rounded-full h-4 overflow-hidden">
                <div className="h-full bg-stone-700 rounded-full" style={{ width: `${Math.abs(dim.spearman_rho! * 100)}%` }} />
              </div>
              <span className="w-16 text-right text-xs font-mono text-stone-500">{dim.spearman_rho!.toFixed(3)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="text-xs text-stone-400">
        报告生成时间: {report.created_at}
      </div>
    </div>
  );
}
