'use client';

interface ScoreCategory {
  [key: string]: any;
}

type CategoryKey = 'hook' | 'messaging' | 'trust' | 'conversion' | 'emotion' | 'production' | 'innovation';

interface ScoringData {
  scoring?: {
    overall_score: number;
    tier: string;
    tier_color: string;
    score_breakdown_note: string;
    hook: ScoreCategory;
    messaging: ScoreCategory;
    trust: ScoreCategory;
    conversion: ScoreCategory;
    emotion: ScoreCategory;
    production: ScoreCategory;
    innovation: ScoreCategory;
    category_rationales?: Array<{
      category: string;
      score: number;
      reason?: string;
      evidence_ids?: string[];
    }>;
  };
  creative_dna?: {
    narrative_template: string;
    emotion_formula: string;
    hook_structure: string;
    target_archetype: string;
    reusable_elements: string[];
  };
  swipe_tags?: string[];
}

const CATEGORY_LABELS: Record<CategoryKey, { label: string; weight: string; dims: string[] }> = {
  hook: { label: '钩子', weight: '20%', dims: ['hook_type_score', 'opening_impact', 'curiosity_gap'] },
  messaging: { label: '信息传递', weight: '20%', dims: ['usp_clarity', 'claim_credibility', 'differentiation'] },
  conversion: { label: '转化设计', weight: '20%', dims: ['cta_clarity', 'urgency', 'low_barrier'] },
  emotion: { label: '情绪调动', weight: '15%', dims: ['emotional_intensity', 'emotional_precision', 'resonance'] },
  trust: { label: '信任建立', weight: '10%', dims: ['endorsement_strength', 'social_proof', 'data_backing'] },
  production: { label: '制作水准', weight: '10%', dims: ['visual_quality', 'audio_quality', 'pacing'] },
  innovation: { label: '创新性', weight: '5%', dims: ['creative_freshness', 'category_breakthrough'] },
};

const CATEGORY_ALIASES: Record<CategoryKey, string> = {
  hook: '钩子',
  messaging: '信息',
  conversion: '转化',
  emotion: '情绪',
  trust: '信任',
  production: '制作',
  innovation: '创新',
};

function categoryAvg(cat: ScoreCategory, dims: string[]): number {
  const vals = dims.map((d) => cat[d] as number).filter((v) => typeof v === 'number');
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
}

export default function ScoreCard({ data }: { data: ScoringData | null }) {
  if (!data?.scoring) return null;

  const { scoring, creative_dna: dna, swipe_tags: tags } = data;
  const score = scoring.overall_score;

  const ringStyle = (score: number) => {
    const hue = (score / 100) * 120;
    return `hsl(${hue}, 40%, 45%)`;
  };

  return (
    <div className="mb-8 rounded-xl border border-stone-200 bg-white p-6">
      {/* Overall score */}
      <div className="mb-6 flex items-center gap-6">
        <div
          className="flex h-20 w-20 items-center justify-center rounded-full text-2xl font-bold text-white"
          style={{ background: ringStyle(score) }}
        >
          {score}
        </div>
        <div>
          <p className="text-base font-semibold text-stone-800">{scoring.tier}</p>
          <p className="mt-0.5 text-sm text-stone-500">{scoring.score_breakdown_note}</p>
        </div>
      </div>

      {/* Category bars */}
      <div className="mb-6 space-y-3">
        {Object.entries(CATEGORY_LABELS).map(([key, cat]) => {
          const catData = scoring[key as CategoryKey] || {};
          const dimensionAvg = categoryAvg(catData, cat.dims);
          const rationaleScore = scoring.category_rationales?.find(
            (item) => item.category.includes(CATEGORY_ALIASES[key as CategoryKey]),
          )?.score;
          const avg = dimensionAvg || (typeof rationaleScore === 'number' ? rationaleScore : 0);
          const pct = Math.round((avg / 5) * 100);
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="w-20 text-xs text-stone-500">{cat.label} <span className="text-stone-300">({cat.weight})</span></span>
              <div className="flex-1 h-2 rounded-full bg-stone-100 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, background: ringStyle(avg * 20) }}
                />
              </div>
              <span className="w-6 text-right text-xs text-stone-400">{avg.toFixed(1)}</span>
            </div>
          );
        })}
      </div>

      {/* Creative DNA */}
      {dna && (
        <div className="mb-4 rounded-lg border border-stone-100 bg-stone-50/50 p-4">
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-stone-400">创意 DNA</h3>
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div>
              <span className="text-stone-400">叙事模板：</span>
              <span className="text-stone-700">{dna.narrative_template}</span>
            </div>
            <div>
              <span className="text-stone-400">情绪公式：</span>
              <span className="text-stone-700">{dna.emotion_formula}</span>
            </div>
            <div>
              <span className="text-stone-400">钩子结构：</span>
              <span className="text-stone-700">{dna.hook_structure}</span>
            </div>
            <div>
              <span className="text-stone-400">目标原型：</span>
              <span className="text-stone-700">{dna.target_archetype}</span>
            </div>
          </div>
          {dna.reusable_elements && dna.reusable_elements.length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-stone-400">可复用元素：</span>
              <ul className="mt-1 list-inside list-disc text-xs text-stone-500">
                {dna.reusable_elements.map((el, i) => (
                  <li key={i}>{el}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Swipe tags */}
      {tags && tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag, i) => (
            <span key={i} className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs text-stone-500">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
