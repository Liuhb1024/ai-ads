'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createJob } from '@/lib/api';

const SAMPLE = '3.89 09/30 ... # 元气森林 # 好物推荐 【广告】 https://v.douyin.com/xxxx/ 复制此链接，打开抖音观看';
const URL_RE = /https?:\/\/[^\s<>，。！？；：、]+/i;

export default function ShareIntake() {
  const router = useRouter();
  const [value, setValue] = useState('');
  const [status, setStatus] = useState<'idle' | 'ready' | 'submitting'>('idle');
  const [error, setError] = useState('');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const submitted = useRef(false);

  const submit = async (text: string) => {
    if (submitted.current || !URL_RE.test(text)) return;
    submitted.current = true;
    setStatus('submitting');
    setError('');
    try {
      const job = await createJob(text);
      router.push(job.next_url);
    } catch (err: any) {
      submitted.current = false;
      setStatus('ready');
      setError(err.message || '暂时无法开始分析');
    }
  };

  const schedule = (text: string) => {
    if (timer.current) clearTimeout(timer.current);
    if (!URL_RE.test(text)) {
      setStatus('idle');
      return;
    }
    setStatus('ready');
    timer.current = setTimeout(() => submit(text), 450);
  };

  return (
    <div className="intake-shell">
      <section className="intake-hero">
        <div className="edition-mark">AI·AD / CREATIVE INTELLIGENCE</div>
        <h1>把一条广告，<br /><em>读出它真正的野心。</em></h1>
        <p className="hero-deck">
          粘贴完整分享口令。系统会自动看视频、听口播、拆策略，
          最后交付广告洞察、抖音图文、口播稿与小红书版本。
        </p>
      </section>

      <section className={`paste-desk ${status === 'submitting' ? 'is-working' : ''}`}>
        <div className="desk-index">01 / INTAKE</div>
        <label htmlFor="share-text">粘贴平台分享内容</label>
        <textarea
          id="share-text"
          value={value}
          onChange={(event) => {
            const text = event.target.value;
            setValue(text);
            schedule(text);
          }}
          placeholder={SAMPLE}
          autoFocus
        />
        <div className="desk-footer">
          <span>
            {status === 'submitting'
              ? '已识别链接，正在建立分析档案…'
              : status === 'ready'
                ? '链接已识别，即将自动开始'
                : '支持抖音、小红书、B站、YouTube、快手与视频号'}
          </span>
          <button onClick={() => submit(value)} disabled={!URL_RE.test(value) || status === 'submitting'}>
            {status === 'submitting' ? '处理中' : '立即解析'}
          </button>
        </div>
        {error && <p className="intake-error">{error}</p>}
      </section>

      <section className="workflow-notes">
        <article><b>01</b><span>读取视频</span><p>链接解析、转录与关键画面</p></article>
        <article><b>02</b><span>拆解广告</span><p>钩子、策略、人群与创意 DNA</p></article>
        <article><b>03</b><span>编辑成稿</span><p>抖音图文、口播稿、小红书</p></article>
      </section>
    </div>
  );
}
