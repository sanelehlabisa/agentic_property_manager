import { apiRequest, jsonRequest } from "./client";
import type { Prediction } from "./types";

export const getPredictions = (propertyId: string) =>
  apiRequest<Prediction[]>(`/properties/${propertyId}/predictions`);
export const approvePrediction = (predictionId: string) =>
  jsonRequest<Prediction>(`/predictions/${predictionId}/approve`, "POST");
export const dismissPrediction = (predictionId: string) =>
  jsonRequest<Prediction>(`/predictions/${predictionId}/dismiss`, "POST");
