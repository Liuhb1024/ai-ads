import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI·AD — 广告创意研究室',
  description: '粘贴分享链接，自动生成广告洞察、抖音图文与口播稿',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="site-header">
          <div className="site-header-inner">
            <a href="/" className="brand-lockup">
              <span>AI·AD</span>
              <small>广告创意研究室</small>
            </a>
            <nav>
              <a href="/">新建研究</a>
              <a href="/swipe">灵感档案</a>
              <a href="/ads">历史记录</a>
            </nav>
          </div>
        </header>
        <main className="site-main">{children}</main>
      </body>
    </html>
  );
}
