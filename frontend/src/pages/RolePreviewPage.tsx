import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { Button, Card, CardContent, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

export function RolePreviewPage({ title }: { title: string }) {
  const navigate = useNavigate();

  return (
    <Stack spacing={3}>
      <Button
        startIcon={<ArrowBackRoundedIcon />}
        color="inherit"
        onClick={() => navigate("/")}
        sx={{ alignSelf: "flex-start" }}
      >
        Foundation status
      </Button>
      <Card>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={1.5}>
            <Typography variant="h4">{title}</Typography>
            <Typography color="text.secondary">
              This guarded route is ready for its feature ticket. Data and
              permitted actions will come from the backend API.
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
