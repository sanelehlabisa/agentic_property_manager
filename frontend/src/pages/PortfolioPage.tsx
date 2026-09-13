import AddRoundedIcon from "@mui/icons-material/AddRounded";
import HomeWorkRoundedIcon from "@mui/icons-material/HomeWorkRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
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
import { useNavigate } from "react-router-dom";

import {
  createProperty,
  getProperties,
  type PropertyInput,
} from "../api/properties";
import type { Property } from "../api/types";

const emptyProperty: PropertyInput = {
  name: "",
  address_line_1: "",
  suburb: "",
  city: "",
  postal_code: "",
};

export function PortfolioPage() {
  const navigate = useNavigate();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<PropertyInput>(emptyProperty);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getProperties()
      .then((nextProperties) => {
        setProperties(nextProperties);
        setError(null);
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Could not load properties");
      })
      .finally(() => setLoading(false));
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      const created = await createProperty(form);
      setProperties((current) => [...current, created]);
      setForm(emptyProperty);
      setDialogOpen(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create property");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Stack spacing={4}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        sx={{ justifyContent: "space-between", gap: 2 }}
      >
        <Box>
          <Typography variant="h4">Property portfolio</Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            Manage property components, maintenance history, and tenant reports.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddRoundedIcon />}
          onClick={() => setDialogOpen(true)}
          sx={{ alignSelf: { xs: "stretch", sm: "center" } }}
        >
          Add property
        </Button>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}
      {loading ? (
        <CircularProgress />
      ) : properties.length === 0 ? (
        <Alert severity="info">Create your first property to get started.</Alert>
      ) : (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "repeat(2, 1fr)" },
            gap: 2,
          }}
        >
          {properties.map((property) => (
            <Card key={property.id}>
              <CardActionArea onClick={() => navigate(`/properties/${property.id}`)}>
                <CardContent sx={{ p: 3 }}>
                  <Stack direction="row" spacing={2} sx={{ alignItems: "flex-start" }}>
                    <HomeWorkRoundedIcon color="primary" />
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>
                        {property.name}
                      </Typography>
                      <Typography color="text.secondary">
                        {property.address_line_1}, {property.suburb}, {property.city}
                      </Typography>
                      <Typography variant="caption" color="primary">
                        {property.access_role}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Box>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth>
        <Stack component="form" onSubmit={submit}>
          <DialogTitle>Add property</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ pt: 1 }}>
              <TextField
                label="Property name"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                required
              />
              <TextField
                label="Street address"
                value={form.address_line_1}
                onChange={(event) =>
                  setForm({ ...form, address_line_1: event.target.value })
                }
                required
              />
              <TextField
                label="Suburb"
                value={form.suburb}
                onChange={(event) => setForm({ ...form, suburb: event.target.value })}
                required
              />
              <TextField
                label="City"
                value={form.city}
                onChange={(event) => setForm({ ...form, city: event.target.value })}
                required
              />
              <TextField
                label="Postal code"
                value={form.postal_code}
                onChange={(event) =>
                  setForm({ ...form, postal_code: event.target.value })
                }
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={saving}>
              {saving ? "Saving..." : "Create property"}
            </Button>
          </DialogActions>
        </Stack>
      </Dialog>
    </Stack>
  );
}
