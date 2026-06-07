'use client';

import { useState } from 'react';
import { confirmJobMetadata, JobState } from '@/lib/api';

const INDUSTRIES = ['美妆', '食品', '3C', '教育', '电商', '金融', '游戏', '其他'];

export default function MetadataConfirmation({ job, onResume }: { job: JobState; onResume: () => void }) {
  const [form, setForm] = useState({
    brand_name: job.brand_name || '',
    product_name: job.product_name || '',
    industry: job.industry === '其他' ? '' : job.industry || '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fields = new Set(job.missing_fields || []);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await confirmJobMetadata(job.id, form);
      onResume();
    } catch (err: any) {
      setError(err.message || '确认失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="confirm-sheet">
      <div className="confirm-media">
        {job.thumbnail_url && <img src={job.thumbnail_url} alt="" />}
        <span>需要你确认</span>
      </div>
      <form onSubmit={submit}>
        <p className="eyebrow">EDITOR CHECK / 只差最后一点信息</p>
        <h2>我们不想靠猜测写稿。</h2>
        <p>视频已经读取完成，只需补齐缺失字段，分析会自动继续。</p>
        {fields.has('brand_name') && (
          <label>品牌名<input value={form.brand_name} onChange={(e) => setForm({ ...form, brand_name: e.target.value })} required /></label>
        )}
        {fields.has('product_name') && (
          <label>产品名<input value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })} required /></label>
        )}
        {fields.has('industry') && (
          <label>行业<select value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} required>
            <option value="">请选择</option>
            {INDUSTRIES.filter((i) => i !== '其他').map((i) => <option key={i}>{i}</option>)}
          </select></label>
        )}
        {error && <p className="intake-error">{error}</p>}
        <button disabled={saving}>{saving ? '继续分析中…' : '确认并继续'}</button>
      </form>
    </div>
  );
}
