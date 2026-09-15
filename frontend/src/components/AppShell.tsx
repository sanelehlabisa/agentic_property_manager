import HomeWorkRoundedIcon from "@mui/icons-material/HomeWorkRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import {
  AppBar,
  Avatar,
  Box,
  Button,
  ButtonBase,
  Container,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { roleHome } from "../auth/session";

export function AppShell() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const roleLabel = user?.role.replace("_", " ");
  const accountSummary = user ? (
    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
      <Avatar sx={{ bgcolor: "grey.200", color: "text.primary" }}>
        <PersonRoundedIcon />
      </Avatar>
      <Box sx={{ display: { xs: "none", md: "block" }, textAlign: "left" }}>
        <Typography variant="body2" sx={{ fontWeight: 800 }}>
          Hello, {user.name.split(" ")[0]}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {user.email} | {roleLabel}
        </Typography>
      </Box>
    </Stack>
  ) : null;

  const leaveSession = () => {
    signOut();
    navigate("/sign-in");
  };

  return (
    <Box sx={{ minHeight: "100vh" }}>
      <AppBar position="static" color="inherit" elevation={0}>
        <Toolbar
          sx={{
            borderBottom: 1,
            borderColor: "divider",
            gap: { xs: 1, md: 2 },
            minHeight: { xs: 72, md: 80 },
            py: 1,
          }}
        >
          <Button
            aria-label="Go to dashboard"
            color="inherit"
            onClick={() => user && navigate(roleHome(user.role))}
            sx={{ mr: "auto", minWidth: 0, p: 0, textTransform: "none" }}
          >
            <Box
              sx={{
                alignItems: "center",
                bgcolor: "primary.main",
                borderRadius: 2,
                color: "primary.contrastText",
                display: "flex",
                height: 40,
                justifyContent: "center",
                mr: 1.25,
                width: 40,
              }}
            >
              <HomeWorkRoundedIcon />
            </Box>
            <Typography
              variant="h6"
              sx={{ display: { xs: "none", sm: "block" }, fontWeight: 900 }}
            >
              Property Manager
            </Typography>
          </Button>
          {user && (
            <Button
              color="inherit"
              onClick={() => navigate(roleHome(user.role))}
              sx={{ display: { xs: "none", md: "inline-flex" } }}
            >
              Dashboard
            </Button>
          )}
          {user?.role === "provider" ? (
            <Tooltip title="Edit profile and services">
              <ButtonBase
                aria-label="Edit profile and services"
                onClick={() => navigate("/provider/profile")}
                sx={{ borderRadius: 2, p: 0.5 }}
              >
                {accountSummary}
              </ButtonBase>
            </Tooltip>
          ) : (
            accountSummary
          )}
          <Button
            color="error"
            variant="outlined"
            startIcon={<LogoutRoundedIcon />}
            onClick={leaveSession}
          >
            Sign out
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: { xs: 4, md: 7 } }}>
        <Outlet />
      </Container>
    </Box>
  );
}
