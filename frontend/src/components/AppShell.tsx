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

import { clearSessionRole, getSessionRole } from "../auth/session";

export function AppShell() {
  const navigate = useNavigate();
  const role = getSessionRole();

  const leavePreview = () => {
    clearSessionRole();
    navigate("/");
  };

  return (
    <Box sx={{ minHeight: "100vh" }}>
      <AppBar position="static" color="inherit" elevation={0}>
        <Toolbar sx={{ borderBottom: 1, borderColor: "divider", gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 800 }}>
            Property Manager
          </Typography>
          {role && <Chip label={role.replace("_", " ")} color="primary" />}
          <Button
            color="inherit"
            startIcon={<LogoutRoundedIcon />}
            onClick={leavePreview}
          >
            Leave preview
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: { xs: 4, md: 7 } }}>
        <Outlet />
      </Container>
    </Box>
  );
}
