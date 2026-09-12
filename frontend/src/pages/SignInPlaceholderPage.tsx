import { Button, Container, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

export function SignInPlaceholderPage() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="sm" sx={{ py: 10 }}>
      <Stack spacing={2}>
        <Typography variant="h4">Sign-in comes next</Typography>
        <Typography color="text.secondary">
          Email onboarding belongs to FE-02. For now, use a role preview from
          the foundation page.
        </Typography>
        <Button variant="contained" onClick={() => navigate("/")}>
          Choose a preview
        </Button>
      </Stack>
    </Container>
  );
}
