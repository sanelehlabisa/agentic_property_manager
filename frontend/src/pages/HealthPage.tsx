import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import ConstructionRoundedIcon from "@mui/icons-material/ConstructionRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getHealth, type HealthResponse } from "../api/health";
import {
  roleHome,
  setSessionRole,
  type UserRole,
} from "../auth/session";

type HealthState =
  | { status: "loading" }
  | { status: "ready"; data: HealthResponse }
  | { status: "unavailable"; message: string };

const previews: Array<{ role: UserRole; label: string }> = [
  { role: "manager", label: "Manager preview" },
  { role: "tenant", label: "Tenant preview" },
  { role: "provider", label: "Provider preview" },
];

export function HealthPage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthState>({ status: "loading" });

  useEffect(() => {
    getHealth()
      .then((data) => setHealth({ status: "ready", data }))
      .catch((error: unknown) =>
        setHealth({
          status: "unavailable",
          message: error instanceof Error ? error.message : "API unavailable",
        }),
      );
  }, []);

  const openPreview = (role: UserRole) => {
    setSessionRole(role);
    navigate(roleHome(role));
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 5, md: 10 } }}>
      <Stack spacing={5}>
        <Stack spacing={2} sx={{ maxWidth: 760 }}>
          <Chip
            icon={<ConstructionRoundedIcon />}
            label="Proof of concept"
            color="primary"
            variant="outlined"
            sx={{ alignSelf: "flex-start" }}
          />
          <Typography variant="h1">Maintenance, handled before it grows.</Typography>
          <Typography color="text.secondary" sx={{ fontSize: "1.15rem" }}>
            Report property issues, approve the work, and connect with the right
            local service provider.
          </Typography>
        </Stack>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "0.9fr 1.1fr" },
            gap: 3,
          }}
        >
          <Card>
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="h6" sx={{ fontWeight: 800 }}>
                  System status
                </Typography>
                {health.status === "loading" && (
                  <Stack
                    direction="row"
                    spacing={2}
                    sx={{ alignItems: "center" }}
                  >
                    <CircularProgress size={22} />
                    <Typography color="text.secondary">Checking API...</Typography>
                  </Stack>
                )}
                {health.status === "ready" && (
                  <Alert severity="success" icon={<CheckCircleRoundedIcon />}>
                    API and database are ready.
                  </Alert>
                )}
                {health.status === "unavailable" && (
                  <Alert severity="warning">
                    Backend unavailable: {health.message}
                  </Alert>
                )}
              </Stack>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Stack spacing={2.5}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>
                    Role-aware foundation
                  </Typography>
                  <Typography color="text.secondary">
                    Preview the guarded landing route for each user type.
                  </Typography>
                </Box>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
                  {previews.map(({ role, label }) => (
                    <Button
                      key={role}
                      variant={role === "manager" ? "contained" : "outlined"}
                      onClick={() => openPreview(role)}
                    >
                      {label}
                    </Button>
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Box>
      </Stack>
    </Container>
  );
}
