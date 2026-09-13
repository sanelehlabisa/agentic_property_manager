import type { UserRole } from "../auth/session";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

export type PropertyAccessRole = "owner" | "manager" | "tenant";

export interface Property {
  id: string;
  name: string;
  address_line_1: string;
  address_line_2: string | null;
  suburb: string;
  city: string;
  postal_code: string | null;
  access_role: PropertyAccessRole;
  created_at: string;
  updated_at: string;
}

export interface ServiceCategory {
  code: string;
  name: string;
  description: string;
}

export type ComponentCondition = "new" | "good" | "fair" | "poor" | "unknown";

export interface Component {
  id: string;
  property_id: string;
  category_code: string;
  name: string;
  installed_on: string | null;
  condition: ComponentCondition;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceRecord {
  id: string;
  component_id: string;
  completed_on: string;
  cost: string;
  provider_name: string | null;
  notes: string | null;
  created_at: string;
}

export type ReportUrgency = "low" | "medium" | "high" | "emergency";
export type ReportStatus =
  | "pending_approval"
  | "approved"
  | "rejected"
  | "converted_to_job";

export interface IssueReport {
  id: string;
  property_id: string;
  reporter_user_id: string;
  reporter_name: string | null;
  component_id: string | null;
  category_code: string;
  title: string;
  description: string;
  urgency: ReportUrgency;
  status: ReportStatus;
  review_reason: string | null;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImportPreviewRow {
  row_number: number;
  completed_on: string | null;
  cost: string | null;
  description: string;
  category_code: string | null;
  component_id: string | null;
  component_name: string | null;
  errors: string[];
}

export interface ImportPreview {
  rows: ImportPreviewRow[];
  valid_count: number;
  error_count: number;
}
