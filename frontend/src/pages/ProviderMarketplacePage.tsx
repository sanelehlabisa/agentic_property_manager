import EditRoundedIcon from "@mui/icons-material/EditRounded";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useEffect, useState } from "react";

import { getCategories } from "../api/properties";
import {
  createBid,
  getAwards,
  getMatchedJobs,
  getProviderProfile,
  type BidInput,
  type ProviderProfileInput,
  updateBid,
  updateProviderProfile,
  updateProviderServices,
  withdrawBid,
} from "../api/provider";
import type {
  Job,
  MatchedJob,
  ProviderProfile,
  ServiceCategory,
} from "../api/types";

const money = new Intl.NumberFormat("en-ZA", {
  style: "currency",
  currency: "ZAR",
});

const emptyProfile: ProviderProfileInput = {
  business_name: "",
  description: "",
  phone: "",
  suburb: "",
  city: "",
  service_radius_km: 25,
};

export function ProviderMarketplacePage() {
  const [profile, setProfile] = useState<ProviderProfile | null>(null);
  const [profileForm, setProfileForm] = useState<ProviderProfileInput>(emptyProfile);
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [activeCategories, setActiveCategories] = useState<Set<string>>(new Set());
  const [jobs, setJobs] = useState<MatchedJob[]>([]);
  const [awards, setAwards] = useState<Job[]>([]);
  const [bidding, setBidding] = useState<MatchedJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    Promise.all([
      getCategories(),
      getProviderProfile().catch(() => null),
      getMatchedJobs().catch(() => []),
      getAwards().catch(() => []),
    ])
      .then(([nextCategories, nextProfile, nextJobs, nextAwards]) => {
        setCategories(nextCategories);
        setProfile(nextProfile);
        setJobs(nextJobs);
        setAwards(nextAwards);
        if (nextProfile) {
          setProfileForm({
            business_name: nextProfile.business_name,
            description: nextProfile.description,
            phone: nextProfile.phone,
            suburb: nextProfile.suburb,
            city: nextProfile.city,
            service_radius_km: nextProfile.service_radius_km,
          });
          setActiveCategories(
            new Set(
              nextProfile.services
                .filter((service) => service.active)
                .map((service) => service.category_code),
            ),
          );
        }
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

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateProviderProfile(profileForm);
      setProfile(updated);
      setSuccess("Provider profile saved.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save profile");
    } finally {
      setBusy(false);
    }
  };

  const saveServices = async () => {
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateProviderServices(
        categories
          .filter((category) => activeCategories.has(category.code))
          .map((category) => ({
            category_code: category.code,
            description: category.description,
            active: true,
          })),
      );
      setProfile(updated);
      await refreshJobs();
      setSuccess("Active services updated; matched jobs refreshed.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save services");
    } finally {
      setBusy(false);
    }
  };

  const toggleCategory = (code: string) => {
    setActiveCategories((current) => {
      const next = new Set(current);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
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
          Profile and matched jobs
        </Typography>
        <Typography color="text.secondary">
          Keep your coverage and services current, then bid on matching open work.
        </Typography>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}
      {success && <Alert severity="success">{success}</Alert>}

      <Card>
        <CardContent sx={{ p: { xs: 2.5, md: 3.5 } }}>
          <Stack component="form" spacing={2.5} onSubmit={saveProfile}>
            <Stack
              direction={{ xs: "column", md: "row" }}
              sx={{ justifyContent: "space-between", gap: 2 }}
            >
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 800 }}>
                  Business profile
                </Typography>
                <Typography color="text.secondary">
                  Your city and active services determine which jobs match.
                </Typography>
              </Box>
              {profile && <Chip color="primary" label={`${profile.rating} rating`} />}
            </Stack>
            <TextField
              required
              label="Business name"
              value={profileForm.business_name}
              onChange={(event) =>
                setProfileForm((current) => ({
                  ...current,
                  business_name: event.target.value,
                }))
              }
            />
            <TextField
              required
              multiline
              minRows={3}
              label="Service description"
              value={profileForm.description}
              onChange={(event) =>
                setProfileForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
            />
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                required
                fullWidth
                label="Phone"
                value={profileForm.phone}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, phone: event.target.value }))
                }
              />
              <TextField
                required
                fullWidth
                label="Suburb"
                value={profileForm.suburb}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, suburb: event.target.value }))
                }
              />
              <TextField
                required
                fullWidth
                label="City"
                value={profileForm.city}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, city: event.target.value }))
                }
              />
              <TextField
                required
                fullWidth
                type="number"
                label="Radius (km)"
                value={profileForm.service_radius_km}
                onChange={(event) =>
                  setProfileForm((current) => ({
                    ...current,
                    service_radius_km: Number(event.target.value),
                  }))
                }
                slotProps={{ htmlInput: { min: 1, max: 500 } }}
              />
            </Stack>
            <Button type="submit" variant="contained" disabled={busy} sx={{ alignSelf: "start" }}>
              Save profile
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ p: { xs: 2.5, md: 3.5 } }}>
          <Stack spacing={2}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800 }}>
                Active services
              </Typography>
              <Typography color="text.secondary">
                Only active categories are used by backend matching.
              </Typography>
            </Box>
            <Box sx={{ display: "grid", gridTemplateColumns: { sm: "1fr 1fr" } }}>
              {categories.map((category) => (
                <FormControlLabel
                  key={category.code}
                  control={
                    <Checkbox
                      checked={activeCategories.has(category.code)}
                      onChange={() => toggleCategory(category.code)}
                    />
                  }
                  label={category.name}
                />
              ))}
            </Box>
            <Button
              variant="outlined"
              disabled={busy || !profile}
              onClick={() => void saveServices()}
              sx={{ alignSelf: "start" }}
            >
              Update services
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Box>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 2 }}>
          Matched open jobs
        </Typography>
        {!profile ? (
          <Alert severity="info">Save your profile before selecting services and bidding.</Alert>
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
