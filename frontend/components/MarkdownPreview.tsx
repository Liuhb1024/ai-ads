'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useState } from 'react';
import { exportPdfUrl } from '@/lib/api';

interface Props {
  id: string;
  content: string;
}

export default function MarkdownPreview({ id, content }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = content;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <section className="report-module">
      <div className="report-command-bar">
        <div>
          <span>REPORT OUTPUT</span>
          <strong>专业研究报告</strong>
        </div>
        <div className="report-actions">
        <button
          onClick={handleCopy}
          className={copied ? 'report-action is-complete' : 'report-action'}
        >
          {copied ? '已复制' : '复制 MD'}
        </button>
          <a className="report-action" href={`/api/jobs/${id}/export.md`} download>
            下载 MD
          </a>
          <a className="report-action primary" href={exportPdfUrl(id)} download>
            导出 PDF
          </a>
        </div>
      </div>
      <article className="report-paper">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </article>
    </section>
  );
}
