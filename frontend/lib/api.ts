const BASE_URL = '/api';

export interface AdCreateInput {
  ad_title?: string;
  brand_name: string;
  product_name?: string;
  industry: string;
  price_range?: string;
  ad_copy?: string;
  scene_description?: string;
  screenshot_description?: string;
  user_context?: string;
  seen_at?: string;
  platform: string;
}

export interface AdSummary {
  id: string;
  brand_name: string;
  product_name?: string;
  industry: string;
  platform: string;
  status: string;
  created_at: string;
  one_sentence_takeaway?: string;
}

export interface AdDetail {
  id: string;
  status: string;
  ad_title?: string;
  brand_name: string;
  product_name?: string;
  industry: string;
  price_range?: string;
  ad_copy?: string;
  scene_description?: string;
  screenshot_description?: string;
  user_context?: string;
  seen_at?: string;
  platform: string;
  analysis?: any;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export async function createAd(data: AdCreateInput): Promise<{ id: string; status: string; created_at: string }> {
  const res = await fetch(`${BASE_URL}/ads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || '创建失败');
  }
  return res.json();
}

export async function listAds(limit = 20, offset = 0): Promise<{ total: number; items: AdSummary[] }> {
  const res = await fetch(`${BASE_URL}/ads?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error('获取列表失败');
  return res.json();
}

// Calibration API

export interface ExpertScoreRequest {
  ad_id: string;
  expert_id: string;
  overall_score: number;
  hook_score: number;
  messaging_score: number;
  conversion_score: number;
  emotion_score: number;
  trust_score: number;
  production_score: number;
  innovation_score: number;
  notes?: string;
}

export interface CalibrationReport {
  n_ads: number;
  n_experts: number;
  overall_spearman_rho: number | null;
  overall_p_value: number | null;
  per_dimension: Array<{ dimension: string; label: string; spearman_rho: number | null; p_value: number | null; n_pairs: number; ai_mean: number; expert_mean: number; correlation_label: string }>;
  expert_reliability: Record<string, number | null>;
  tier_agreement: number | null;
  created_at: string;
}

export async function submitExpertScore(data: ExpertScoreRequest): Promise<void> {
  const res = await fetch(`${BASE_URL}/calibration/scores`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || '提交失败'); }
}

export async function listExpertScores(expertId?: string): Promise<{ scores: any[]; count: number }> {
  const params = expertId ? `?expert_id=${expertId}` : '';
  const res = await fetch(`${BASE_URL}/calibration/scores${params}`);
  if (!res.ok) throw new Error('获取失败');
  return res.json();
}

export async function fetchCalibrationReport(): Promise<CalibrationReport> {
  const res = await fetch(`${BASE_URL}/calibration/report`);
  if (!res.ok) throw new Error('获取报告失败');
  return res.json();
}

export async function getAd(id: string): Promise<AdDetail> {
  const res = await fetch(`${BASE_URL}/ads/${id}`);
  if (!res.ok) throw new Error('获取详情失败');
  return res.json();
}

export async function analyzeAd(id: string): Promise<{ status: string; result?: any }> {
  const res = await fetch(`${BASE_URL}/ads/${id}/analyze`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || '分析失败');
  }
  return res.json();
}

export async function getAnalysis(id: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/ads/${id}/analysis`);
  if (!res.ok) throw new Error('获取分析结果失败');
  return res.json();
}

export async function exportMarkdownUrl(id: string): Promise<string> {
  return `${BASE_URL}/jobs/${id}/export.md`;
}

export function exportPdfUrl(id: string): string {
  return `${BASE_URL}/jobs/${id}/export.pdf`;
}

export interface ParseLinkResult {
  url: string;
  platform: string;
  title: string;
  author: string;
  description: string;
  thumbnail_url: string;
  parsed: boolean;
  error: string;
}

export async function parseLink(url: string): Promise<ParseLinkResult> {
  const res = await fetch(`${BASE_URL}/parse-link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || '解析链接失败');
  }
  return res.json();
}

export interface JobState {
  id: string;
  status: string;
  stage: string;
  progress_message: string;
  source_url?: string;
  source_platform?: string;
  parsed_title?: string;
  parsed_author?: string;
  thumbnail_url?: string;
  brand_name?: string;
  product_name?: string;
  industry?: string;
  missing_fields: string[];
  analysis?: any;
  publishing?: any;
  error_message?: string;
  failed_stage?: string;
  created_at: string;
  updated_at: string;
}

export async function createJob(shareText: string): Promise<{ id: string; status: string; stage: string; next_url: string }> {
  const res = await fetch(`${BASE_URL}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ share_text: shareText }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || '无法创建分析任务');
  }
  return res.json();
}

export async function getJob(id: string): Promise<JobState> {
  const res = await fetch(`${BASE_URL}/jobs/${id}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('无法获取任务状态');
  return res.json();
}

export async function confirmJobMetadata(
  id: string,
  values: { brand_name?: string; product_name?: string; industry?: string },
): Promise<void> {
  const res = await fetch(`${BASE_URL}/jobs/${id}/metadata`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(values),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || '提交确认信息失败');
  }
}

export async function retryJob(id: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/jobs/${id}/retry`, { method: 'POST' });
  if (!res.ok) throw new Error('重试失败');
}

export interface SearchResult extends AdSummary {
  _score: number;
}

export interface CompareResponse {
  ad_a: CompareSide;
  ad_b: CompareSide;
  predicted_winner: string;
  confidence: string;
  key_differences: string[];
  analysis_markdown: string;
  hook_comparison: string;
  audience_comparison: string;
  trust_comparison: string;
}

export interface CompareSide {
  ad_id: string;
  brand_name: string;
  product_name: string;
  platform: string;
  industry: string;
  overall_score: number;
  tier: string;
  strengths: string[];
  weaknesses: string[];
}

export async function compareAds(adIdA: string, adIdB: string): Promise<CompareResponse> {
  const res = await fetch(`${BASE_URL}/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ad_id_a: adIdA, ad_id_b: adIdB }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || '对比失败');
  }
  return res.json();
}

export async function searchAds(query: string, topK = 20): Promise<{ items: SearchResult[]; total: number; query: string }> {
  const params = new URLSearchParams({ q: query, top_k: String(topK) });
  const res = await fetch(`${BASE_URL}/ads/search?${params}`);
  if (!res.ok) throw new Error('搜索失败');
  return res.json();
}
