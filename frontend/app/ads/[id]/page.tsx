'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getAd, AdDetail } from '@/lib/api';
import AnalysisResult from '@/components/AnalysisResult';
import ScoreCard from '@/components/ScoreCard';

export default function AdDetailPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const [ad, setAd] = useState<AdDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAd();
  }, [id]);

  const loadAd = async () => {
    setLoading(true);
    try {
      const data = await getAd(id);
      setAd(data);
    } catch (err: any) {
      setError(err.message || '加载详情失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="mx-auto h-1.5 w-48 overflow-hidden rounded-full bg-stone-100">
          <div className="h-full w-2/3 animate-pulse rounded-full bg-stone-300" />
        </div>
      </div>
    );
  }

  if (error || !ad) {
    return (
      <div className="py-20 text-center">
        <p className="mb-4 text-sm text-red-600">{error || '未找到记录'}</p>
        <Link href="/" className="text-sm text-stone-500 underline underline-offset-2 hover:text-stone-900">
          返回首页
        </Link>
      </div>
    );
  }

  const metaItems = [
    { label: '行业', value: ad.industry },
    { label: '平台', value: ad.platform },
    { label: '价格带', value: ad.price_range },
    { label: '看到时间', value: ad.seen_at },
  ].filter((item) => item.value);

  return (
    <div>
      <div className="mb-6">
        <Link href="/ads" className="text-sm text-stone-400 no-underline transition-colors hover:text-stone-600">
          ← 返回列表
        </Link>
      </div>

      <h1 className="mb-6 text-2xl font-semibold tracking-tight">
        {ad.brand_name}
        {ad.product_name && (
          <span className="ml-2 text-lg font-normal text-stone-400">{ad.product_name}</span>
        )}
      </h1>

      <div className="mb-8 grid grid-cols-2 gap-x-8 gap-y-3 rounded-xl border border-stone-200 bg-white p-5 text-sm sm:grid-cols-4">
        {metaItems.map((item) => (
          <div key={item.label}>
            <span className="text-xs font-medium uppercase tracking-wider text-stone-400">{item.label}</span>
            <p className="mt-0.5 text-stone-700">{item.value}</p>
          </div>
        ))}
        {ad.ad_title && (
          <div className="col-span-full">
            <span className="text-xs font-medium uppercase tracking-wider text-stone-400">标题</span>
            <p className="mt-0.5 text-stone-700">{ad.ad_title}</p>
          </div>
        )}
        {ad.ad_copy && (
          <div className="col-span-full">
            <span className="text-xs font-medium uppercase tracking-wider text-stone-400">文案</span>
            <p className="mt-0.5 text-stone-700">
              {ad.ad_copy.length > 200 ? ad.ad_copy.slice(0, 200) + '...' : ad.ad_copy}
            </p>
          </div>
        )}
        {ad.user_context && (
          <div className="col-span-full">
            <span className="text-xs font-medium uppercase tracking-wider text-stone-400">用户补充</span>
            <p className="mt-0.5 text-stone-700">{ad.user_context}</p>
          </div>
        )}
        <div className="col-span-full mt-1 text-xs text-stone-400">
          创建时间：{ad.created_at}
        </div>
      </div>

      <ScoreCard data={ad.analysis?.scoring || null} />

      <AnalysisResult
        adId={ad.id}
        initialStatus={ad.status}
        initialAnalysis={ad.analysis}
      />
    </div>
  );
}
