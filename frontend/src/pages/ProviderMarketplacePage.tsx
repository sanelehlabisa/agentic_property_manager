import EditRoundedIcon from "@mui/icons-material/EditRounded";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useEffect, useState } from "react";

import {
  createBid,
  getAwards,
  getMatchedJobs,
  getProviderProfile,
  type BidInput,
  updateBid,
  withdrawBid,
} from "../api/provider";
import type { Job, MatchedJob } from "../api/types";

const money = new Intl.NumberFormat("en-ZA", {
  style: "currency",
  currency: "ZAR",
});

export function ProviderMarketplacePage() {
  const [profileReady, setProfileReady] = useState(true);
  const [jobs, setJobs] = useState<MatchedJob[]>([]);
  const [awards, setAwards] = useState<Job[]>([]);
  const [bidding, setBidding] = useState<MatchedJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    Promise.all([
      getProviderProfile()
        .then(() => true)
        .catch(() => false),
      getMatchedJobs().catch(() => []),
      getAwards().catch(() => []),
    ])
      .then(([nextProfileReady, nextJobs, nextAwards]) => {
        setProfileReady(nextProfileReady);
        setJobs(nextJobs);
        setAwards(nextAwards);
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Could not load marketplace");
      })
      .finally(() => setLoading(false));
  }, []);

  const refreshJobs = async () => {
    const [nextJobs, nextAwards] = await Promise.all([getMatchedJobs(), getAwards()]);
    setJobs(nextJobs);
    setAwards(nextAwards);
  };

  if (loading) {
    return (
      <Box sx={{ py: 10, textAlign: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="overline" color="primary" sx={{ fontWeight: 800 }}>
          Service provider
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 900 }}>
          Jobs and awarded work
        </Typography>
        <Typography color="text.secondary">
          Bid on matching open work and keep track of jobs you have won.
        </Typography>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}
      {success && <Alert severity="success">{success}</Alert>}

      <Box>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 2 }}>
          Matched open jobs
        </Typography>
        {!profileReady ? (
          <Alert
            severity="info"
            action={
              <Button color="inherit" size="small" href="/provider/profile">
                Create profile
              </Button>
            }
          >
            Create your profile and select services before bidding.
          </Alert>
        ) : jobs.length === 0 ? (
          <Typography color="text.secondary">
            No open jobs match your active categories and city.
          </Typography>
        ) : (
          <Stack spacing={2}>
            {jobs.map((job) => (
              <Card key={job.id} variant="outlined">
                <CardContent>
                  <Stack spacing={1.5}>
                    <Stack direction="row" sx={{ gap: 1, flexWrap: "wrap" }}>
                      <Chip color="primary" size="small" label={job.category_code} />
                      <Chip variant="outlined" size="small" label={job.public_location} />
                      {job.own_bid_status && (
                        <Chip size="small" color="success" label={`bid ${job.own_bid_status}`} />
                      )}
                    </Stack>
                    <Typography variant="h6" sx={{ fontWeight: 800 }}>
                      {job.description}
                    </Typography>
                    <Typography color="text.secondary">
                      Client budget: {money.format(Number(job.budget))}
                    </Typography>
                    {job.own_bid_status === "submitted" ? (
                      <Stack direction="row" spacing={1}>
                        <Button
                          startIcon={<EditRoundedIcon />}
                          onClick={() => setBidding(job)}
                        >
                          Update bid
                        </Button>
                        <Button
                          color="error"
                          disabled={busy}
                          onClick={() => {
                            if (!job.own_bid_id) return;
                            setBusy(true);
                            withdrawBid(job.own_bid_id)
                              .then(refreshJobs)
                              .catch((caught) =>
                                setError(
                                  caught instanceof Error
                                    ? caught.message
                                    : "Could not withdraw bid",
                                ),
                              )
                              .finally(() => setBusy(false));
                          }}
                        >
                          Withdraw
                        </Button>
                      </Stack>
                    ) : job.own_bid_status ? (
                      <Typography variant="body2" color="text.secondary">
                        This bid is {job.own_bid_status}.
                      </Typography>
                    ) : (
                      <Button
                        variant="contained"
                        startIcon={<SendRoundedIcon />}
                        onClick={() => setBidding(job)}
                        sx={{ alignSelf: "start" }}
                      >
                        Submit bid
                      </Button>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Box>

      {awards.length > 0 && (
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 800, mb: 2 }}>
            Awarded work
          </Typography>
          <Stack spacing={1}>
            {awards.map((job) => (
              <Alert key={job.id} severity="success">
                {job.description} · {job.public_location} · {job.status}
              </Alert>
            ))}
          </Stack>
        </Box>
      )}

      <BidDialog
        job={bidding}
        onClose={() => setBidding(null)}
        onSaved={async () => {
          setBidding(null);
          await refreshJobs();
          setSuccess("Bid saved.");
        }}
      />
    </Stack>
  );
}

function BidDialog({
  job,
  onClose,
  onSaved,
}: {
  job: MatchedJob | null;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [form, setForm] = useState<BidInput>({
    amount: "",
    message: "",
    available_on: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!job) return;
    const frame = window.requestAnimationFrame(() => {
      setForm({
        amount: job.own_bid_amount ?? "",
        message: job.own_bid_message ?? "",
        available_on: job.own_bid_available_on ?? "",
      });
      setError("");
    });
    return () => window.cancelAnimationFrame(frame);
  }, [job]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!job) return;
    setBusy(true);
    setError("");
    try {
      if (job.own_bid_id) await updateBid(job.own_bid_id, form);
      else await createBid(job.id, form);
      await onSaved();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save bid");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={Boolean(job)} onClose={busy ? undefined : onClose} fullWidth maxWidth="sm">
      <Stack component="form" onSubmit={submit}>
        <DialogTitle>{job?.own_bid_id ? "Update bid" : "Submit bid"}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              required
              type="number"
              label="Amount (ZAR)"
              value={form.amount}
              onChange={(event) =>
                setForm((current) => ({ ...current, amount: event.target.value }))
              }
              slotProps={{ htmlInput: { min: 0.01, step: "0.01" } }}
            />
            <TextField
              required
              multiline
              minRows={3}
              label="Message"
              value={form.message}
              onChange={(event) =>
                setForm((current) => ({ ...current, message: event.target.value }))
              }
            />
            <TextField
              required
              type="date"
              label="Available on"
              value={form.available_on}
              onChange={(event) =>
                setForm((current) => ({ ...current, available_on: event.target.value }))
              }
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={busy}>
            {busy ? "Saving..." : "Save bid"}
          </Button>
        </DialogActions>
      </Stack>
    </Dialog>
  );
}
