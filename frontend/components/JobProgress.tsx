const STAGES = [
  ['resolving', '识别分享链接'],
  ['media', '读取视频与声音'],
  ['identifying', '确认品牌与产品'],
  ['analyzing', '拆解广告策略'],
  ['publishing', '编辑发布文稿'],
  ['completed', '完成交付'],
];

export default function JobProgress({ stage, message }: { stage: string; message: string }) {
  const activeIndex = STAGES.findIndex(([key]) => key === stage);
  return (
    <div className="progress-sheet">
      <div className="progress-kicker">PROCESS / 分析进度</div>
      <h2>{message || '正在建立广告档案'}</h2>
      <ol>
        {STAGES.map(([key, label], index) => {
          const done = activeIndex > index || stage === 'completed';
          const active = activeIndex === index;
          return (
            <li key={key} className={done ? 'done' : active ? 'active' : ''}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <b>{label}</b>
              <i>{done ? '完成' : active ? '进行中' : '等待'}</i>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
