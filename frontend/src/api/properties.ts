import { apiRequest, jsonRequest } from "./client";
import type {
  Component,
  ComponentCondition,
  ImportPreview,
  MaintenanceRecord,
  Property,
  ServiceCategory,
} from "./types";

export interface PropertyInput {
  name: string;
  address_line_1: string;
  address_line_2?: string;
  suburb: string;
  city: string;
  postal_code?: string;
}

export interface ComponentInput {
  category_code: string;
  name: string;
  installed_on?: string;
  condition: ComponentCondition;
}

export interface MaintenanceRecordInput {
  completed_on: string;
  cost: string;
  provider_name?: string;
  notes?: string;
}

export const getProperties = () => apiRequest<Property[]>("/properties");
export const getProperty = (id: string) => apiRequest<Property>(`/properties/${id}`);
export const createProperty = (data: PropertyInput) =>
  jsonRequest<Property>("/properties", "POST", data);
export const getCategories = () =>
  apiRequest<ServiceCategory[]>("/service-categories");
export const getComponents = (propertyId: string) =>
  apiRequest<Component[]>(`/properties/${propertyId}/components`);
export const createComponent = (propertyId: string, data: ComponentInput) =>
  jsonRequest<Component>(`/properties/${propertyId}/components`, "POST", data);
export const getMaintenanceRecords = (componentId: string) =>
  apiRequest<MaintenanceRecord[]>(`/components/${componentId}/maintenance-records`);
export const createMaintenanceRecord = (
  componentId: string,
  data: MaintenanceRecordInput,
) =>
  jsonRequest<MaintenanceRecord>(
    `/components/${componentId}/maintenance-records`,
    "POST",
    data,
  );
export const previewMaintenanceImport = (propertyId: string, csvText: string) =>
  jsonRequest<ImportPreview>(
    `/properties/${propertyId}/maintenance-imports/preview`,
    "POST",
    { csv_text: csvText },
  );
export const confirmMaintenanceImport = (
  propertyId: string,
  rows: Array<{
    completed_on: string;
    cost: string;
    component_id: string;
    description?: string;
  }>,
) =>
  jsonRequest<MaintenanceRecord[]>(
    `/properties/${propertyId}/maintenance-imports/confirm`,
    "POST",
    { rows },
  );
