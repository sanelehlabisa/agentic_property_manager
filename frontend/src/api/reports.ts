import { apiRequest, jsonRequest } from "./client";
import type { IssueReport, ReportUrgency } from "./types";

export interface IssueReportInput {
  component_id?: string;
  category_code: string;
  title: string;
  description: string;
  urgency: ReportUrgency;
}

export const getReports = (propertyId: string) =>
  apiRequest<IssueReport[]>(`/properties/${propertyId}/reports`);
export const createReport = (propertyId: string, data: IssueReportInput) =>
  jsonRequest<IssueReport>(`/properties/${propertyId}/reports`, "POST", data);
export const approveReport = (reportId: string) =>
  jsonRequest<IssueReport>(`/reports/${reportId}/approve`, "POST");
export const rejectReport = (reportId: string, reason: string) =>
  jsonRequest<IssueReport>(`/reports/${reportId}/reject`, "POST", { reason });
