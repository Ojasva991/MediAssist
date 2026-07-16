import { Badge } from "@/components/ui/badge";

const SEVERITY_MAP = {
  low: { variant: "success", label: "Low severity" },
  moderate: { variant: "warning", label: "Moderate severity" },
  high: { variant: "danger", label: "High severity" },
  emergency: { variant: "danger", label: "Emergency" },
};

export function SeverityBadge({ severity }) {
  if (!severity) return null;
  const key = String(severity).toLowerCase();
  const config = SEVERITY_MAP[key] ?? { variant: "neutral", label: severity };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
