import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import {
  AppBar,
  Box,
  Button,
  Chip,
  Container,
  Toolbar,
  Typography,
} from "@mui/material";
import { Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { roleHome } from "../auth/session";

export function AppShell() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  const leaveSession = () => {
    signOut();
    navigate("/sign-in");
  };

  return (
    <Box sx={{ minHeight: "100vh" }}>
      <AppBar position="static" color="inherit" elevation={0}>
        <Toolbar sx={{ borderBottom: 1, borderColor: "divider", gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 800 }}>
            Property Manager
          </Typography>
          {user && (
            <Button color="inherit" onClick={() => navigate(roleHome(user.role))}>
              Dashboard
            </Button>
          )}
          {user?.role === "provider" && (
            <Button color="inherit" onClick={() => navigate("/provider/profile")}>
              Profile & services
            </Button>
          )}
          {user && <Chip label={user.role.replace("_", " ")} color="primary" />}
          <Button
            color="inherit"
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
