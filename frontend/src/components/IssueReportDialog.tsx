import { useState } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from "@mui/material";

import { createReport } from "../api/reports";
import type {
  Component,
  IssueReport,
  ReportUrgency,
  ServiceCategory,
} from "../api/types";

interface IssueReportDialogProps {
  propertyId: string;
  categories: ServiceCategory[];
  components: Component[];
  open: boolean;
  onClose: () => void;
  onCreated: (report: IssueReport) => void;
}

export function IssueReportDialog({
  propertyId,
  categories,
  components,
  open,
  onClose,
  onCreated,
}: IssueReportDialogProps) {
  const [categoryCode, setCategoryCode] = useState("");
  const [componentId, setComponentId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [urgency, setUrgency] = useState<ReportUrgency>("medium");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const selectedCategoryCode = categoryCode || categories[0]?.code || "";

  const reset = () => {
    setComponentId("");
    setTitle("");
    setDescription("");
    setUrgency("medium");
    setError("");
  };

  const close = () => {
    if (submitting) return;
    reset();
    onClose();
  };

  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const report = await createReport(propertyId, {
        category_code: selectedCategoryCode,
        component_id: componentId || undefined,
        title: title.trim(),
        description: description.trim(),
        urgency,
      });
      reset();
      onCreated(report);
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not submit report");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={close} fullWidth maxWidth="sm">
      <DialogTitle>Report a property issue</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <FormControl fullWidth required>
            <InputLabel id="report-category-label">Service category</InputLabel>
            <Select
              labelId="report-category-label"
              label="Service category"
              value={selectedCategoryCode}
              onChange={(event) => setCategoryCode(event.target.value)}
            >
              {categories.map((category) => (
                <MenuItem key={category.code} value={category.code}>
                  {category.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel id="report-component-label">Component (optional)</InputLabel>
            <Select
              labelId="report-component-label"
              label="Component (optional)"
              value={componentId}
              onChange={(event) => setComponentId(event.target.value)}
            >
              <MenuItem value="">None</MenuItem>
              {components.map((component) => (
                <MenuItem key={component.id} value={component.id}>
                  {component.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            required
            label="Issue title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <TextField
            required
            multiline
            minRows={4}
            label="What happened?"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <FormControl fullWidth>
            <InputLabel id="report-urgency-label">Urgency</InputLabel>
            <Select
              labelId="report-urgency-label"
              label="Urgency"
              value={urgency}
              onChange={(event) => setUrgency(event.target.value as ReportUrgency)}
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="emergency">Emergency</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={close} disabled={submitting}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={submit}
          disabled={
            submitting || !selectedCategoryCode || !title.trim() || !description.trim()
          }
        >
          {submitting ? "Submitting..." : "Submit report"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
