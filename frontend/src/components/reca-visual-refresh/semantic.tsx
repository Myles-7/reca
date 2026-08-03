import {
  BadgeCheck,
  Bot,
  Circle,
  CircleAlert,
  CircleCheck,
  CircleDashed,
  CircleX,
  Clock3,
  FileCheck2,
  Quote,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  UserRoundCheck,
} from "lucide-react"

import { cn } from "@/lib/utils"

export type VisualSemanticTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "degraded"
  | "unknown"
  | "evidence"
  | "approval"
  | "ai-suggestion"

const tones = new Set<VisualSemanticTone>([
  "neutral",
  "info",
  "success",
  "warning",
  "danger",
  "degraded",
  "unknown",
  "evidence",
  "approval",
  "ai-suggestion",
])

export function normalizeVisualTone(tone: string): VisualSemanticTone {
  return tones.has(tone as VisualSemanticTone)
    ? (tone as VisualSemanticTone)
    : "unknown"
}

const toneIcons = {
  neutral: Circle,
  info: CircleAlert,
  success: CircleCheck,
  warning: TriangleAlert,
  danger: CircleX,
  degraded: CircleDashed,
  unknown: CircleAlert,
  evidence: Quote,
  approval: ShieldCheck,
  "ai-suggestion": Sparkles,
} satisfies Record<VisualSemanticTone, typeof Circle>

export function StatusBadge({
  label,
  tone = "unknown",
  title,
  className,
}: {
  label: string
  tone?: string
  title?: string
  className?: string
}) {
  const normalized = normalizeVisualTone(tone)
  const Icon = toneIcons[normalized]
  return (
    <span
      className={cn("reca-status-badge", `reca-tone-${normalized}`, className)}
      title={title}
      data-tone={normalized}
    >
      <Icon aria-hidden="true" />
      <span className="reca-status-badge__label">{label}</span>
    </span>
  )
}

export type SourceKind =
  | "verified"
  | "evidence"
  | "human-decision"
  | "approval"
  | "ai-suggestion"
  | "degraded"
  | "unknown"

const sourceDefinition = {
  verified: { tone: "success", icon: BadgeCheck },
  evidence: { tone: "evidence", icon: FileCheck2 },
  "human-decision": { tone: "info", icon: UserRoundCheck },
  approval: { tone: "approval", icon: ShieldCheck },
  "ai-suggestion": { tone: "ai-suggestion", icon: Bot },
  degraded: { tone: "degraded", icon: TriangleAlert },
  unknown: { tone: "unknown", icon: Clock3 },
} satisfies Record<
  SourceKind,
  { tone: VisualSemanticTone; icon: typeof Circle }
>

export function SourceBadge({
  label,
  kind = "unknown",
  title,
  className,
}: {
  label: string
  kind?: SourceKind
  title?: string
  className?: string
}) {
  const definition = sourceDefinition[kind] ?? sourceDefinition.unknown
  const Icon = definition.icon
  return (
    <span
      className={cn(
        "reca-source-badge",
        `reca-tone-${definition.tone}`,
        className,
      )}
      title={title}
      data-source-kind={kind}
    >
      <Icon aria-hidden="true" />
      <span className="reca-source-badge__label">{label}</span>
    </span>
  )
}
