'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listAds, AdSummary } from '@/lib/api';

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  pending:    { label: '待分析', className: 'bg-stone-100 text-stone-500' },
  analyzing:  { label: '分析中', className: 'bg-amber-50 text-amber-600' },
  completed:  { label: '已完成', className: 'bg-emerald-50 text-emerald-700' },
  failed:     { label: '失败',   className: 'bg-red-50 text-red-600' },
};

export default function AdsHistory() {
  const [ads, setAds] = useState<AdSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAds();
  }, []);

  const loadAds = async () => {
    try {
      const data = await listAds();
      setAds(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const statusBadge = (s: string) => STATUS_MAP[s] || STATUS_MAP.pending;

  return (
    <div>
      <h1 className="mb-8 text-2xl font-semibold tracking-tight">历史分析</h1>

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-xl border border-stone-200 bg-white p-5">
              <div className="mb-2 h-4 w-40 rounded bg-stone-100" />
              <div className="h-3 w-56 rounded bg-stone-50" />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button onClick={loadAds} className="ml-3 underline underline-offset-2">重试</button>
        </div>
      )}

      {!loading && !error && ads.length === 0 && (
        <div className="py-20 text-center">
          <p className="mb-4 text-sm text-stone-400">暂无分析记录</p>
          <Link href="/" className="text-sm font-medium text-stone-900 underline underline-offset-2 hover:text-stone-600">
            创建第一条分析 →
          </Link>
        </div>
      )}

      {!loading && ads.length > 0 && (
        <>
          <div className="space-y-3">
            {ads.map((ad) => {
              const badge = statusBadge(ad.status);
              return (
                <Link
                  key={ad.id}
                  href={`/ads/${ad.id}`}
                  className="block rounded-xl border border-stone-200 bg-white p-5 no-underline text-inherit transition-shadow hover:shadow-sm"
                >
                  <div className="mb-1 flex items-center justify-between">
                    <div className="text-base font-semibold">
                      {ad.brand_name}
                      {ad.product_name && (
                        <span className="ml-2 font-normal text-stone-400">{ad.product_name}</span>
                      )}
                    </div>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.className}`}>
                      {badge.label}
                    </span>
                  </div>
                  <div className="text-xs text-stone-400">
                    {ad.industry} · {ad.platform} · {ad.created_at}
                  </div>
                  {ad.one_sentence_takeaway && (
                    <p className="mt-2 text-sm italic text-stone-500">
                      {ad.one_sentence_takeaway}
                    </p>
                  )}
                </Link>
              );
            })}
          </div>
          <p className="mt-6 text-center text-xs text-stone-400">共 {total} 条</p>
        </>
      )}
    </div>
  );
}
