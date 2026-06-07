'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { listAds, searchAds, AdSummary } from '@/lib/api';

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  completed: { label: '已完成', className: 'bg-emerald-50 text-emerald-700' },
  analyzing: { label: '分析中', className: 'bg-amber-50 text-amber-600' },
  failed: { label: '失败', className: 'bg-red-50 text-red-600' },
  pending: { label: '待分析', className: 'bg-stone-100 text-stone-500' },
};

const INDUSTRY_FILTERS = ['全部', '美妆', '食品', '3C', '教育', '电商', '金融', '游戏', '其他'];
const PLATFORM_FILTERS = ['全部', '抖音', '小红书', '视频号', '快手', '其他'];

export default function SwipeFilePage() {
  const [ads, setAds] = useState<AdSummary[]>([]);
  const [searchResults, setSearchResults] = useState<AdSummary[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [industryFilter, setIndustryFilter] = useState('全部');
  const [platformFilter, setPlatformFilter] = useState('全部');
  const [searchQuery, setSearchQuery] = useState('');
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    loadAds();
  }, []);

  // Semantic search with debounce
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await searchAds(searchQuery.trim(), 50);
        setSearchResults(data.items);
      } catch {
        // fall back to client-side filtering on error
        setSearchResults(null);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [searchQuery]);

  const loadAds = async () => {
    setLoading(true);
    try {
      const data = await listAds(50);
      setAds(data.items);
    } catch (err: any) {
      setError(err.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const sourceAds = searchResults ?? ads;
  const isLoading = loading || searching;

  const filtered = sourceAds.filter((ad) => {
    if (industryFilter !== '全部' && ad.industry !== industryFilter) return false;
    if (platformFilter !== '全部' && ad.platform !== platformFilter) return false;
    return true;
  });

  const completedAds = filtered.filter((a) => a.status === 'completed');
  const filterChip = (label: string, active: boolean, onClick: () => void) => (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
        active
          ? 'bg-stone-900 text-white'
          : 'bg-stone-100 text-stone-500 hover:bg-stone-200'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div>
      <div className="mb-8">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight">Swipe File</h1>
        <p className="text-sm text-stone-500">
          灵感库 · 已完成分析的广告可在此浏览、筛选、搜索
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-3">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="搜索品牌、品类、洞察..."
          className="w-full rounded-lg border border-stone-200 bg-white px-4 py-2.5 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-400 focus:outline-none focus:ring-1 focus:ring-stone-400 transition-colors"
        />
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-stone-400 self-center mr-1">行业：</span>
          {INDUSTRY_FILTERS.map((f) => (
            <span key={f}>{filterChip(f, industryFilter === f, () => setIndustryFilter(f))}</span>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-stone-400 self-center mr-1">平台：</span>
          {PLATFORM_FILTERS.map((f) => (
            <span key={f}>{filterChip(f, platformFilter === f, () => setPlatformFilter(f))}</span>
          ))}
        </div>
      </div>

      {isLoading && (
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
        </div>
      )}

      {!isLoading && !error && completedAds.length === 0 && (
        <div className="py-20 text-center">
          <p className="mb-4 text-sm text-stone-400">
            {ads.length === 0 ? '暂无广告记录' : '没有符合条件的广告'}
          </p>
          <Link
            href="/"
            className="text-sm font-medium text-stone-900 underline underline-offset-2 hover:text-stone-600"
          >
            {ads.length === 0 ? '创建第一条分析 →' : '清除筛选'}
          </Link>
        </div>
      )}

      {!isLoading && completedAds.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {completedAds.map((ad) => {
            const badge = STATUS_MAP[ad.status] || STATUS_MAP.pending;
            return (
              <Link
                key={ad.id}
                href={`/ads/${ad.id}`}
                className="group flex flex-col rounded-xl border border-stone-200 bg-white p-5 no-underline text-inherit transition-shadow hover:shadow-sm"
              >
                <div className="mb-2 flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold text-stone-800 group-hover:text-stone-900">
                      {ad.brand_name}
                    </p>
                    {ad.product_name && (
                      <p className="text-xs text-stone-400">{ad.product_name}</p>
                    )}
                  </div>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${badge.className}`}>
                    {badge.label}
                  </span>
                </div>

                {ad.one_sentence_takeaway && (
                  <p className="mb-3 line-clamp-2 text-xs italic text-stone-500">
                    {ad.one_sentence_takeaway}
                  </p>
                )}

                <div className="mt-auto flex items-center gap-2 text-[10px] text-stone-400">
                  <span>{ad.industry}</span>
                  <span>·</span>
                  <span>{ad.platform}</span>
                  <span>·</span>
                  <span>{ad.created_at}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {!isLoading && completedAds.length > 0 && (
        <p className="mt-6 text-center text-xs text-stone-400">
          共 {completedAds.length} 条（过滤后）
        </p>
      )}
    </div>
  );
}
