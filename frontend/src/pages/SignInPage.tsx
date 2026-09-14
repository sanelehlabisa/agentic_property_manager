import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { roleHome, type UserRole } from "../auth/session";

const demoAccounts = [
  ["Homeowner", "owner@example.com"],
  ["Manager", "manager@example.com"],
  ["Tenant", "tenant@example.com"],
  ["Provider", "provider@example.com"],
  ["Provider 2", "provider2@example.com"],
] as const;

export function SignInPage() {
  const navigate = useNavigate();
  const { user, signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<UserRole>("homeowner");
  const [onboarding, setOnboarding] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) return <Navigate to={roleHome(user.role)} replace />;

  const authenticate = async (selectedEmail: string, details?: boolean) => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await signIn(
        selectedEmail,
        details ? { name: name.trim(), role } : undefined,
      );
      if (result.requiresOnboarding) {
        setEmail(selectedEmail);
        setOnboarding(true);
      } else if (result.user) {
        navigate(roleHome(result.user.role));
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sign-in failed");
    } finally {
      setSubmitting(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void authenticate(email.trim(), onboarding);
  };

  return (
    <Container maxWidth="sm" sx={{ py: { xs: 5, md: 10 } }}>
      <Card>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack component="form" spacing={3} onSubmit={submit}>
            <Box>
              <Chip label="Demo access" color="primary" variant="outlined" />
              <Typography variant="h4" sx={{ mt: 2 }}>
                {onboarding ? "Create your profile" : "Welcome back"}
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 1 }}>
                {onboarding
                  ? "Choose one role for this proof-of-concept account."
                  : "Enter an email address. No password is required for this demo."}
              </Typography>
            </Box>

            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              label="Email address"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={onboarding || submitting}
              required
              fullWidth
            />
            {onboarding && (
              <>
                <TextField
                  label="Full name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required
                  fullWidth
                />
                <TextField
                  select
                  label="Role"
                  value={role}
                  onChange={(event) => setRole(event.target.value as UserRole)}
                  fullWidth
                >
                  <MenuItem value="homeowner">Homeowner</MenuItem>
                  <MenuItem value="manager">Property manager</MenuItem>
                  <MenuItem value="tenant">Tenant</MenuItem>
                  <MenuItem value="provider">Service provider</MenuItem>
                </TextField>
              </>
            )}
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? "Please wait..." : onboarding ? "Create account" : "Continue"}
            </Button>

            {!onboarding && (
              <Box>
                <Typography variant="overline" color="text.secondary">
                  Seeded demo accounts
                </Typography>
                <Stack direction="row" sx={{ flexWrap: "wrap", gap: 1, mt: 1 }}>
                  {demoAccounts.map(([label, accountEmail]) => (
                    <Button
                      key={accountEmail}
                      size="small"
                      variant="outlined"
                      disabled={submitting}
                      onClick={() => void authenticate(accountEmail)}
                    >
                      {label}
                    </Button>
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Container>
  );
}
