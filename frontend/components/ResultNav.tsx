import Link from 'next/link';

export default function ResultNav({ id, active }: { id: string; active: string }) {
  const items = [
    ['insight', '洞察报告'],
    ['douyin', '抖音成稿'],
    ['xiaohongshu', '小红书版本'],
  ];
  return (
    <nav className="result-nav">
      {items.map(([key, label], index) => (
        <Link key={key} href={`/jobs/${id}/${key}`} className={active === key ? 'active' : ''}>
          <span>0{index + 1}</span>{label}
        </Link>
      ))}
    </nav>
  );
}
