const BASE_URL = '/api';
const DEFAULT_TIMEOUT_MS = 15_000;

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('请求超时，请确认后端服务正常后重试');
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

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
  const res = await fetchWithTimeout(`${BASE_URL}/ads`, {
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
  const res = await fetchWithTimeout(`${BASE_URL}/ads?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error('获取列表失败');
  return res.json();
}

export async function getAd(id: string): Promise<AdDetail> {
  const res = await fetchWithTimeout(`${BASE_URL}/ads/${id}`);
  if (!res.ok) throw new Error('获取详情失败');
  return res.json();
}

export async function analyzeAd(id: string): Promise<{ status: string; result?: any }> {
  const res = await fetchWithTimeout(`${BASE_URL}/ads/${id}/analyze`, { method: 'POST' }, 120_000);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || '分析失败');
  }
  return res.json();
}

export async function getAnalysis(id: string): Promise<any> {
  const res = await fetchWithTimeout(`${BASE_URL}/ads/${id}/analysis`);
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
  const res = await fetchWithTimeout(`${BASE_URL}/parse-link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  }, 45_000);
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
  video_status?: string;
  created_at: string;
  updated_at: string;
}

export async function createJob(shareText: string): Promise<{ id: string; status: string; stage: string; next_url: string }> {
  const res = await fetchWithTimeout(`${BASE_URL}/jobs`, {
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
  const res = await fetchWithTimeout(`${BASE_URL}/jobs/${id}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('无法获取任务状态');
  return res.json();
}

export async function confirmJobMetadata(
  id: string,
  values: { brand_name?: string; product_name?: string; industry?: string },
): Promise<void> {
  const res = await fetchWithTimeout(`${BASE_URL}/jobs/${id}/metadata`, {
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
  const res = await fetchWithTimeout(`${BASE_URL}/jobs/${id}/retry`, { method: 'POST' });
  if (!res.ok) throw new Error('重试失败');
}

export interface SearchResult extends AdSummary {
  _score: number;
}

export async function searchAds(query: string, topK = 20): Promise<{ items: SearchResult[]; total: number; query: string }> {
  const params = new URLSearchParams({ q: query, top_k: String(topK) });
  const res = await fetchWithTimeout(`${BASE_URL}/ads/search?${params}`, {}, 45_000);
  if (!res.ok) throw new Error('搜索失败');
  return res.json();
}


// Video generation API

export interface VideoStatusResponse {
  status: string;  // "" | "generating" | "completed" | "failed"
  video_url: string;
  error?: string | null;
}

export async function generateVideo(adId: string): Promise<{ status: string; video_url: string }> {
  const res = await fetchWithTimeout(`${BASE_URL}/jobs/${adId}/video`, { method: 'POST' }, 10_000);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || '视频生成请求失败');
  }
  return res.json();
}

export async function getVideoStatus(adId: string): Promise<VideoStatusResponse> {
  const res = await fetchWithTimeout(`${BASE_URL}/jobs/${adId}/video`, {}, 10_000);
  if (!res.ok) throw new Error('获取视频状态失败');
  return res.json();
}

export function videoDownloadUrl(adId: string): string {
  return `${BASE_URL}/jobs/${adId}/video.mp4`;
}
