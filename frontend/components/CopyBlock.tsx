'use client';

import { useState } from 'react';

export default function CopyBlock({ label, content }: { label: string; content: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(content);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = content;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <section className="copy-block">
      <header>
        <span>{label}</span>
        <button onClick={copy}>{copied ? '已复制' : '复制'}</button>
      </header>
      <div className="copy-content">{content}</div>
    </section>
  );
}
