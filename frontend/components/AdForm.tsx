'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createAd, parseLink, ParseLinkResult } from '@/lib/api';

const INDUSTRIES = ['美妆', '食品', '3C', '教育', '电商', '金融', '游戏', '其他'];
const PRICE_RANGES = ['', '低价', '中价', '高价', '免费', '不清楚'];
const PLATFORMS = ['抖音', '小红书', '视频号', '快手', '其他'];

export default function AdForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [linkUrl, setLinkUrl] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parsed, setParsed] = useState<ParseLinkResult | null>(null);
  const [showManual, setShowManual] = useState(true);

  const [form, setForm] = useState({
    brand_name: '',
    product_name: '',
    industry: '',
    price_range: '',
    platform: '',
    ad_title: '',
    ad_copy: '',
    scene_description: '',
    screenshot_description: '',
    user_context: '',
    seen_at: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleParseLink = async () => {
    if (!linkUrl.trim()) return;
    setParsing(true);
    setError('');
    try {
      const result = await parseLink(linkUrl.trim());
      if (result.parsed) {
        setParsed(result);
        setForm({
          ...form,
          ad_title: result.title || form.ad_title,
          ad_copy: result.description || form.ad_copy,
          platform: result.platform || form.platform,
        });
        setShowManual(true);
      } else {
        setError(result.error || '未能解析该链接，请使用手动表单');
      }
    } catch (err: any) {
      setError(err.message || '解析链接失败');
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!form.brand_name || !form.industry || !form.platform) {
      setError('请填写品牌名、行业和平台来源');
      return;
    }

    setLoading(true);
    try {
      const data: any = { ...form, source_url: linkUrl || undefined };
      Object.keys(data).forEach((k) => {
        if (data[k] === '') data[k] = undefined;
      });
      const result = await createAd(data);
      router.push(`/ads/${result.id}`);
    } catch (err: any) {
      setError(err.message || '提交失败');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full rounded-lg border border-stone-200 bg-white px-4 py-2.5 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-400 focus:outline-none focus:ring-1 focus:ring-stone-400 transition-colors";
  const labelClass = "mb-1.5 block text-xs font-medium uppercase tracking-wider text-stone-400";

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-10">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight">新建广告分析</h1>
        <p className="text-sm text-stone-500">
          粘贴视频链接自动解析，或手动填写信息。当前为 Mock 模式。
        </p>
      </div>

      {/* Link input */}
      <div className="mb-8 rounded-xl border border-stone-200 bg-white p-6">
        <label className={labelClass}>视频链接</label>
        <div className="flex gap-3">
          <input
            type="url"
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleParseLink(); } }}
            placeholder="粘贴抖音/小红书/视频号/YouTube/B站 分享链接"
            className={inputClass + ' flex-1'}
          />
          <button
            onClick={handleParseLink}
            disabled={parsing || !linkUrl.trim()}
            className="rounded-lg bg-stone-900 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
          >
            {parsing ? '解析中...' : '解析链接'}
          </button>
        </div>

        {/* Parsed result */}
        {parsed && (
          <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-medium text-emerald-700">解析成功</span>
              <button
                onClick={() => { setParsed(null); setLinkUrl(''); }}
                className="text-xs text-stone-400 hover:text-stone-600"
              >
                清除
              </button>
            </div>
            {parsed.thumbnail_url && (
              <img
                src={parsed.thumbnail_url}
                alt=""
                className="mb-3 h-32 w-full rounded-lg object-cover"
              />
            )}
            <p className="text-sm font-medium text-stone-800">{parsed.title}</p>
            {parsed.author && (
              <p className="mt-0.5 text-xs text-stone-500">@{parsed.author} · {parsed.platform}</p>
            )}
            {parsed.description && (
              <p className="mt-2 line-clamp-3 text-xs text-stone-500">{parsed.description}</p>
            )}
          </div>
        )}

        {!parsed && !parsing && (
          <p className="mt-2 text-xs text-stone-400">
            支持抖音、TikTok、小红书、B站、YouTube 等平台。解析失败时可手动填写。
          </p>
        )}
      </div>

      {/* Manual form — always shown but collapsible */}
      {!showManual && (
        <button
          onClick={() => setShowManual(true)}
          className="w-full rounded-xl border border-dashed border-stone-300 bg-white/50 py-10 text-center text-sm text-stone-400 transition-colors hover:border-stone-400 hover:text-stone-600"
        >
          展开手动填写表单
        </button>
      )}

      {showManual && (
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mb-4 flex justify-end">
            <button
              type="button"
              onClick={() => setShowManual(false)}
              className="text-xs text-stone-400 hover:text-stone-600"
            >
              收起表单
            </button>
          </div>

          <div className="rounded-xl border border-stone-200 bg-white p-6">
            <div className="mb-6 grid grid-cols-2 gap-x-6 gap-y-5">
              <div>
                <label className={labelClass}>品牌名 *</label>
                <input name="brand_name" value={form.brand_name} onChange={handleChange} className={inputClass} placeholder="如 欧莱雅" />
              </div>
              <div>
                <label className={labelClass}>商品名</label>
                <input name="product_name" value={form.product_name} onChange={handleChange} className={inputClass} placeholder="如 复颜玻尿酸颈霜" />
              </div>
              <div>
                <label className={labelClass}>行业 *</label>
                <select name="industry" value={form.industry} onChange={handleChange} className={inputClass}>
                  <option value="">请选择</option>
                  {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
              <div>
                <label className={labelClass}>价格带</label>
                <select name="price_range" value={form.price_range} onChange={handleChange} className={inputClass}>
                  {PRICE_RANGES.map((p) => <option key={p} value={p}>{p || '不选择'}</option>)}
                </select>
              </div>
              <div>
                <label className={labelClass}>平台来源 *</label>
                <select name="platform" value={form.platform} onChange={handleChange} className={inputClass}>
                  <option value="">请选择</option>
                  {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label className={labelClass}>看到时间</label>
                <input name="seen_at" type="date" value={form.seen_at} onChange={handleChange} className={inputClass} />
              </div>
            </div>

            <div className="mb-5">
              <label className={labelClass}>广告标题</label>
              <input name="ad_title" value={form.ad_title} onChange={handleChange} className={inputClass} placeholder="广告投放标题" />
            </div>

            <div className="mb-5">
              <label className={labelClass}>广告文案 / 口播文案</label>
              <textarea name="ad_copy" value={form.ad_copy} onChange={handleChange} rows={4} className={inputClass + ' resize-y'} placeholder="视频中的口播文案或字幕文字" />
            </div>

            <div className="mb-5">
              <label className={labelClass}>视频画面描述</label>
              <textarea name="scene_description" value={form.scene_description} onChange={handleChange} rows={3} className={inputClass + ' resize-y'} placeholder="场景、人物、动作的文字描述" />
            </div>

            <div className="mb-5">
              <label className={labelClass}>截图描述</label>
              <textarea name="screenshot_description" value={form.screenshot_description} onChange={handleChange} rows={3} className={inputClass + ' resize-y'} placeholder="对截图内容的文字描述" />
            </div>

            <div className="mb-5">
              <label className={labelClass}>用户补充背景</label>
              <textarea name="user_context" value={form.user_context} onChange={handleChange} rows={2} className={inputClass + ' resize-y'} placeholder="你知道的额外信息，如品牌近况、行业背景" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-xl bg-stone-900 py-3.5 text-sm font-medium text-white transition-colors hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
          >
            {loading ? '提交中...' : '开始分析'}
          </button>
        </form>
      )}
    </div>
  );
}
