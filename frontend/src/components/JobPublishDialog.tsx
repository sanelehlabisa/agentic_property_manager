import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useEffect, useState } from "react";

import type { JobInput } from "../api/jobs";

interface JobPublishDialogProps {
  open: boolean;
  title: string;
  initialDescription: string;
  initialBudget: string;
  onClose: () => void;
  onPublish: (data: JobInput) => Promise<void>;
}

export function JobPublishDialog({
  open,
  title,
  initialDescription,
  initialBudget,
  onClose,
  onPublish,
}: JobPublishDialogProps) {
  const [description, setDescription] = useState(initialDescription);
  const [budget, setBudget] = useState(initialBudget);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    const frame = window.requestAnimationFrame(() => {
      setDescription(initialDescription);
      setBudget(initialBudget);
      setError("");
    });
    return () => window.cancelAnimationFrame(frame);
  }, [initialBudget, initialDescription, open]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onPublish({ description: description.trim(), budget });
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not publish job");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="sm">
      <Stack component="form" onSubmit={submit}>
        <DialogTitle>{title}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <Typography color="text.secondary">
              Confirm the provider-safe description and maximum budget. The exact street
              address and tenant details will not be published.
            </Typography>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              required
              multiline
              minRows={3}
              label="Public job description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
            <TextField
              required
              type="number"
              label="Budget (ZAR)"
              value={budget}
              onChange={(event) => setBudget(event.target.value)}
              slotProps={{ htmlInput: { min: 0, step: "0.01" } }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={busy || description.trim().length < 5 || budget === ""}
          >
            {busy ? "Publishing..." : "Approve and publish"}
          </Button>
        </DialogActions>
      </Stack>
    </Dialog>
  );
}
