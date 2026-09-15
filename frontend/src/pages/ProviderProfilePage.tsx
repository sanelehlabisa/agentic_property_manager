import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getCategories } from "../api/properties";
import {
  getProviderProfile,
  type ProviderProfileInput,
  updateProviderProfile,
  updateProviderServices,
} from "../api/provider";
import type { ProviderProfile, ServiceCategory } from "../api/types";

const emptyProfile: ProviderProfileInput = {
  business_name: "",
  description: "",
  phone: "",
  suburb: "",
  city: "",
  service_radius_km: 25,
};

export function ProviderProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<ProviderProfile | null>(null);
  const [profileForm, setProfileForm] = useState<ProviderProfileInput>(emptyProfile);
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [activeCategories, setActiveCategories] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    Promise.all([getCategories(), getProviderProfile().catch(() => null)])
      .then(([nextCategories, nextProfile]) => {
        setCategories(nextCategories);
        setProfile(nextProfile);
        if (!nextProfile) return;
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
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Could not load profile");
      })
      .finally(() => setLoading(false));
  }, []);

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
      setSuccess("Active services updated.");
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
        <Button
          startIcon={<ArrowBackRoundedIcon />}
          onClick={() => navigate("/provider/jobs")}
          sx={{ mb: 2 }}
        >
          Back to jobs
        </Button>
        <Typography variant="overline" color="primary" sx={{ fontWeight: 800 }}>
          Account
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 900 }}>
          Profile and services
        </Typography>
        <Typography color="text.secondary">
          Your city and active services determine which jobs match.
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
              <Typography variant="h5" sx={{ fontWeight: 800 }}>
                Business profile
              </Typography>
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
    </Stack>
  );
}
