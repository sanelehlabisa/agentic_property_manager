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
import { useAuth } from "../auth/AuthContext";
import { roleHome } from "../auth/session";

type HealthState =
  | { status: "loading" }
  | { status: "ready"; data: HealthResponse }
  | { status: "unavailable"; message: string };

export function HealthPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
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
                    Continue to your workspace
                  </Typography>
                  <Typography color="text.secondary">
                    Sign in with email to open the workspace allowed for your role.
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  onClick={() => navigate(user ? roleHome(user.role) : "/sign-in")}
                  sx={{ alignSelf: "flex-start" }}
                >
                  {user ? "Open dashboard" : "Sign in"}
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Box>
      </Stack>
    </Container>
  );
}
