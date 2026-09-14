import AddRoundedIcon from "@mui/icons-material/AddRounded";
import HomeWorkRoundedIcon from "@mui/icons-material/HomeWorkRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { getCategories, getComponents, getProperties } from "../api/properties";
import { getReports } from "../api/reports";
import type {
  Component,
  IssueReport,
  Property,
  ServiceCategory,
} from "../api/types";
import { IssueReportDialog } from "../components/IssueReportDialog";
import { ReportStatusChip, UrgencyChip } from "../components/ReportStatusChip";

export function TenantHomePage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [propertyId, setPropertyId] = useState("");
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [components, setComponents] = useState<Component[]>([]);
  const [reports, setReports] = useState<IssueReport[]>([]);
  const [reportDialog, setReportDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getProperties(), getCategories()])
      .then(([nextProperties, nextCategories]) => {
        setProperties(nextProperties);
        setCategories(nextCategories);
        setPropertyId(nextProperties[0]?.id ?? "");
        if (nextProperties.length === 0) setLoading(false);
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Could not load properties");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!propertyId) {
      return;
    }

    Promise.all([getComponents(propertyId), getReports(propertyId)])
      .then(([nextComponents, nextReports]) => {
        setComponents(nextComponents);
        setReports(nextReports);
        setError("");
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Could not load reports");
      })
      .finally(() => setLoading(false));
  }, [propertyId]);

  const selectedProperty = properties.find((property) => property.id === propertyId);

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" color="primary" sx={{ fontWeight: 800 }}>
          Tenant workspace
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 900 }}>
          Property issues
        </Typography>
        <Typography color="text.secondary">
          Report maintenance issues and follow their approval status.
        </Typography>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      {properties.length > 1 && (
        <FormControl sx={{ maxWidth: 420 }}>
          <InputLabel id="tenant-property-label">Property</InputLabel>
          <Select
            labelId="tenant-property-label"
            label="Property"
            value={propertyId}
            onChange={(event) => {
              setLoading(true);
              setPropertyId(event.target.value);
            }}
          >
            {properties.map((property) => (
              <MenuItem key={property.id} value={property.id}>
                {property.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {loading && properties.length === 0 ? (
        <Box sx={{ py: 8, textAlign: "center" }}>
          <CircularProgress />
        </Box>
      ) : !selectedProperty ? (
        <Alert severity="info">
          You have not been assigned to a property yet. Ask the property manager to add
          your tenant account.
        </Alert>
      ) : (
        <>
          <Card variant="outlined">
            <CardContent>
              <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={2}
                sx={{
                  justifyContent: "space-between",
                  alignItems: { xs: "flex-start", sm: "center" },
                }}
              >
                <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
                  <HomeWorkRoundedIcon color="primary" />
                  <Box>
                    <Typography variant="h5" sx={{ fontWeight: 800 }}>
                      {selectedProperty.name}
                    </Typography>
                    <Typography color="text.secondary">
                      {selectedProperty.address_line_1}, {selectedProperty.suburb},{" "}
                      {selectedProperty.city}
                    </Typography>
                  </Box>
                </Stack>
                <Button
                  variant="contained"
                  startIcon={<AddRoundedIcon />}
                  onClick={() => setReportDialog(true)}
                >
                  Report issue
                </Button>
              </Stack>
            </CardContent>
          </Card>

          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, mb: 2 }}>
              My reports
            </Typography>
            {loading ? (
              <CircularProgress size={28} />
            ) : reports.length === 0 ? (
              <Typography color="text.secondary">
                No reports yet. Use “Report issue” when something needs attention.
              </Typography>
            ) : (
              <Stack spacing={2}>
                {reports.map((report) => (
                  <Card key={report.id} variant="outlined">
                    <CardContent>
                      <Stack spacing={1}>
                        <Stack direction="row" sx={{ gap: 1, flexWrap: "wrap" }}>
                          <ReportStatusChip status={report.status} />
                          <UrgencyChip urgency={report.urgency} />
                          {report.job_status && (
                            <Chip
                              size="small"
                              color={report.job_status === "awarded" ? "success" : "primary"}
                              label={`job ${report.job_status.replace("_", " ")}`}
                            />
                          )}
                        </Stack>
                        <Typography variant="h6" sx={{ fontWeight: 800 }}>
                          {report.title}
                        </Typography>
                        <Typography color="text.secondary">{report.description}</Typography>
                        {report.review_reason && (
                          <Alert severity="info">Review note: {report.review_reason}</Alert>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Box>

          <IssueReportDialog
            open={reportDialog}
            propertyId={selectedProperty.id}
            categories={categories}
            components={components}
            onClose={() => setReportDialog(false)}
            onCreated={(report) => setReports((current) => [report, ...current])}
          />
        </>
      )}
    </Stack>
  );
}
