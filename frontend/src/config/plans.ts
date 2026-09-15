import type { BillingMetricCode, PlanCode, PlanDefinition } from "../types";

/** Presentation-only copy. Prices and all entitlement numbers come from GET /api/plans. */
export const PLAN_PRESENTATION: Record<PlanCode, {
  description: string;
  tag?: string;
  featured?: boolean;
}> = {
  free: {
    description: "从零开启 AI 声音与文字陪伴",
    tag: "入门体验",
  },
  plus: {
    description: "深度日常陪伴与克隆声音沉浸体验",
    tag: "推荐",
    featured: true,
  },
  pro: {
    description: "高频语音交互与多重专属音色槽位",
    tag: "深度陪伴",
  },
};

export const QUOTA_METRICS: Array<{
  key: BillingMetricCode;
  planLimit: keyof PlanDefinition["limits"];
  label: string;
}> = [
  { key: "ai_reply", planLimit: "ai_reply", label: "AI 回复" },
  { key: "ai_voice_seconds", planLimit: "ai_voice_seconds", label: "AI 语音" },
  { key: "image", planLimit: "image", label: "图片理解" },
  { key: "video", planLimit: "video", label: "视频理解" },
  { key: "chat_import_batch", planLimit: "chat_import_batch", label: "截图导入" },
  { key: "voice_slot", planLimit: "voice_slots", label: "克隆音色槽位" },
];

const integerFormatter = new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 });
const decimalFormatter = new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 1 });

export function quotaMetricLabel(metric?: BillingMetricCode): string {
  return QUOTA_METRICS.find((item) => item.key === metric)?.label || "套餐额度";
}

export function formatQuotaValue(metric: BillingMetricCode, value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const normalized = metric === "ai_voice_seconds" ? value / 60 : value;
  const amount = Number.isInteger(normalized)
    ? integerFormatter.format(normalized)
    : decimalFormatter.format(normalized);
  const unit = metric === "ai_reply" ? "次"
    : metric === "ai_voice_seconds" ? "分钟"
      : metric === "image" ? "张"
        : metric === "video" ? "条"
          : metric === "chat_import_batch" ? "批"
            : "个";
  return `${amount} ${unit}`;
}

export function planLimitForMetric(plan: PlanDefinition, metric: BillingMetricCode): number {
  const item = QUOTA_METRICS.find((candidate) => candidate.key === metric);
  return item ? plan.limits[item.planLimit] : 0;
}

export function planHighlights(plan: PlanDefinition): string[] {
  return QUOTA_METRICS.map((metric) => {
    const limit = planLimitForMetric(plan, metric.key);
    const amount = limit === 0 && metric.key === "video" ? "暂未开放" : formatQuotaValue(metric.key, limit);
    return `${amount} ${metric.label}`;
  });
}
