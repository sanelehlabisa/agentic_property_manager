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

export type PredictionUrgency = "overdue" | "due_soon" | "upcoming";
export type PredictionStatus =
  | "active"
  | "approved"
  | "dismissed"
  | "converted_to_job";

export interface Prediction {
  id: string;
  component_id: string;
  component_name: string;
  category_code: string;
  due_date: string;
  estimated_cost: string;
  urgency: PredictionUrgency;
  explanation: string;
  status: PredictionStatus;
  created_at: string;
  updated_at: string;
}

export type JobStatus = "open" | "awarded" | "in_progress" | "completed" | "cancelled";

export interface Job {
  id: string;
  property_id: string;
  property_name: string | null;
  category_code: string;
  issue_report_id: string | null;
  prediction_id: string | null;
  description: string;
  budget: string;
  public_location: string;
  status: JobStatus;
  approved_by_user_id: string;
  approved_at: string;
  created_at: string;
  updated_at: string;
}

export type BidStatus = "submitted" | "accepted" | "withdrawn" | "rejected";

export interface ProviderService {
  id: string;
  category_code: string;
  description: string | null;
  active: boolean;
}

export interface ProviderProfile {
  id: string;
  user_id: string;
  business_name: string;
  description: string;
  phone: string;
  suburb: string;
  city: string;
  service_radius_km: number;
  rating: string;
  services: ProviderService[];
  created_at: string;
  updated_at: string;
}

export interface MatchedJob extends Job {
  own_bid_id: string | null;
  own_bid_status: BidStatus | null;
  own_bid_amount: string | null;
  own_bid_message: string | null;
  own_bid_available_on: string | null;
}

export interface Bid {
  id: string;
  job_id: string;
  provider_profile_id: string;
  business_name: string | null;
  provider_rating: string | null;
  amount: string;
  message: string;
  available_on: string;
  status: BidStatus;
  created_at: string;
  updated_at: string;
}
