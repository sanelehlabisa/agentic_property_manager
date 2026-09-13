import { Chip } from "@mui/material";

import type { ReportStatus, ReportUrgency } from "../api/types";

export function ReportStatusChip({ status }: { status: ReportStatus }) {
  const color =
    status === "approved" || status === "converted_to_job"
      ? "success"
      : status === "rejected"
        ? "error"
        : "warning";
  return <Chip size="small" color={color} label={status.replaceAll("_", " ")} />;
}

export function UrgencyChip({ urgency }: { urgency: ReportUrgency }) {
  const color =
    urgency === "emergency" || urgency === "high"
      ? "error"
      : urgency === "medium"
        ? "warning"
        : "default";
  return <Chip size="small" color={color} variant="outlined" label={urgency} />;
}
