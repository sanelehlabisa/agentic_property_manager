import { apiRequest, jsonRequest } from "./client";
import type { Bid, Job, MatchedJob, ProviderProfile } from "./types";

export interface ProviderProfileInput {
  business_name: string;
  description: string;
  phone: string;
  suburb: string;
  city: string;
  service_radius_km: number;
}

export interface ProviderServiceInput {
  category_code: string;
  description?: string;
  active: boolean;
}

export interface BidInput {
  amount: string;
  message: string;
  available_on: string;
}

export const getProviderProfile = () => apiRequest<ProviderProfile>("/provider/profile");
export const updateProviderProfile = (data: ProviderProfileInput) =>
  jsonRequest<ProviderProfile>("/provider/profile", "PUT", data);
export const updateProviderServices = (services: ProviderServiceInput[]) =>
  jsonRequest<ProviderProfile>("/provider/services", "PUT", { services });
export const getMatchedJobs = () =>
  apiRequest<MatchedJob[]>("/provider/matched-jobs");
export const getAwards = () => apiRequest<Job[]>("/provider/awards");
export const createBid = (jobId: string, data: BidInput) =>
  jsonRequest<Bid>(`/jobs/${jobId}/bids`, "POST", data);
export const updateBid = (bidId: string, data: Partial<BidInput>) =>
  jsonRequest<Bid>(`/bids/${bidId}`, "PATCH", data);
export const withdrawBid = (bidId: string) =>
  apiRequest<void>(`/bids/${bidId}`, { method: "DELETE" });
