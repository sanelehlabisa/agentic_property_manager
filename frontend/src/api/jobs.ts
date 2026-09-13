import { apiRequest, jsonRequest } from "./client";
import type { Bid, Job } from "./types";

export interface JobInput {
  description: string;
  budget: string;
}

export const createJobFromReport = (reportId: string, data: JobInput) =>
  jsonRequest<Job>(`/jobs/from-report/${reportId}`, "POST", data);
export const createJobFromPrediction = (predictionId: string, data: JobInput) =>
  jsonRequest<Job>(`/jobs/from-prediction/${predictionId}`, "POST", data);
export const getPropertyJobs = (propertyId: string) =>
  apiRequest<Job[]>(`/properties/${propertyId}/jobs`);
export const getJobBids = (jobId: string) => apiRequest<Bid[]>(`/jobs/${jobId}/bids`);
export const acceptBid = (bidId: string) =>
  jsonRequest<Bid>(`/bids/${bidId}/accept`, "POST");
