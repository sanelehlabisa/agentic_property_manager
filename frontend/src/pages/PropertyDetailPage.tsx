import AddRoundedIcon from "@mui/icons-material/AddRounded";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import UploadFileRoundedIcon from "@mui/icons-material/UploadFileRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  MenuItem,
  Snackbar,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createJobFromPrediction,
  createJobFromReport,
  getPropertyJobs,
  type JobInput,
} from "../api/jobs";
import {
  approvePrediction,
  dismissPrediction,
  getPredictions,
} from "../api/predictions";
import {
  confirmMaintenanceImport,
  createComponent,
  createMaintenanceRecord,
  getCategories,
  getComponents,
  getMaintenanceRecords,
  getProperty,
  previewMaintenanceImport,
} from "../api/properties";
import { approveReport, getReports, rejectReport } from "../api/reports";
import type {
  Component,
  ComponentCondition,
  ImportPreview,
  IssueReport,
  Job,
  MaintenanceRecord,
  Prediction,
  Property,
  ServiceCategory,
} from "../api/types";
import { IssueReportDialog } from "../components/IssueReportDialog";
import { BidReviewDialog } from "../components/BidReviewDialog";
import { JobPublishDialog } from "../components/JobPublishDialog";
import { ReportStatusChip, UrgencyChip } from "../components/ReportStatusChip";

const money = new Intl.NumberFormat("en-ZA", {
  style: "currency",
  currency: "ZAR",
});

type PublishSource =
  | { kind: "report"; item: IssueReport }
  | { kind: "prediction"; item: Prediction };

export function PropertyDetailPage() {
  const { propertyId = "" } = useParams();
  const navigate = useNavigate();
  const [property, setProperty] = useState<Property | null>(null);
  const [components, setComponents] = useState<Component[]>([]);
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [reports, setReports] = useState<IssueReport[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null);
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [componentDialog, setComponentDialog] = useState(false);
  const [recordDialog, setRecordDialog] = useState(false);
  const [reportDialog, setReportDialog] = useState(false);
  const [publishing, setPublishing] = useState<PublishSource | null>(null);
  const [reviewingJob, setReviewingJob] = useState<Job | null>(null);
  const [notice, setNotice] = useState("");
  const [rejecting, setRejecting] = useState<IssueReport | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getProperty(propertyId),
      getComponents(propertyId),
      getCategories(),
      getReports(propertyId),
      getPredictions(propertyId),
      getPropertyJobs(propertyId),
    ])
      .then(
        ([
          propertyData,
          componentData,
          categoryData,
          reportData,
          predictionData,
          jobData,
        ]) => {
        setProperty(propertyData);
        setComponents(componentData);
        setCategories(categoryData);
        setReports(reportData);
        setPredictions(predictionData);
        setJobs(jobData);
        setError(null);
        },
      )
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Could not load property");
      })
      .finally(() => setLoading(false));
  }, [propertyId]);

  const openHistory = async (component: Component) => {
    setSelectedComponent(component);
    try {
      setRecords(await getMaintenanceRecords(component.id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load history");
    }
  };

  const review = async (report: IssueReport, approved: boolean, reason?: string) => {
    setBusy(true);
    try {
      const updated = approved
        ? await approveReport(report.id)
        : await rejectReport(report.id, reason ?? "Not approved");
      setReports((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setRejecting(null);
      setRejectReason("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not review report");
    } finally {
      setBusy(false);
    }
  };

  const dismiss = async (prediction: Prediction) => {
    setBusy(true);
    try {
      const updated = await dismissPrediction(prediction.id);
      setPredictions((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not dismiss prediction");
    } finally {
      setBusy(false);
    }
  };

  const publish = async (data: JobInput) => {
    if (!publishing) return;
    if (publishing.kind === "report") {
      if (publishing.item.status === "pending_approval") {
        await approveReport(publishing.item.id);
      }
      await createJobFromReport(publishing.item.id, data);
    } else {
      if (publishing.item.status === "active") {
        await approvePrediction(publishing.item.id);
      }
      await createJobFromPrediction(publishing.item.id, data);
    }

    const [nextReports, nextPredictions, nextJobs] = await Promise.all([
      getReports(propertyId),
      getPredictions(propertyId),
      getPropertyJobs(propertyId),
    ]);
    setReports(nextReports);
    setPredictions(nextPredictions);
    setJobs(nextJobs);
    setPublishing(null);
  };

  const importFile = async (file: File) => {
    setBusy(true);
    try {
      setPreview(await previewMaintenanceImport(propertyId, await file.text()));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not preview CSV");
    } finally {
      setBusy(false);
    }
  };

  const confirmImport = async () => {
    if (!preview) return;
    const rows = preview.rows
      .filter(
        (row) =>
          row.errors.length === 0 &&
          row.component_id &&
          row.completed_on &&
          row.cost,
      )
      .map((row) => ({
        component_id: row.component_id!,
        completed_on: row.completed_on!,
        cost: row.cost!,
        description: row.description,
      }));
    if (rows.length === 0) {
      setError("No valid rows with a matched component can be imported.");
      return;
    }
    setBusy(true);
    try {
      await confirmMaintenanceImport(propertyId, rows);
      setPreview(null);
      if (selectedComponent) await openHistory(selectedComponent);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not import records");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <CircularProgress />;
  if (!property) return <Alert severity="error">{error ?? "Property not found"}</Alert>;

  return (
    <Stack spacing={4}>
      <Button
        startIcon={<ArrowBackRoundedIcon />}
        color="inherit"
        onClick={() => navigate("/portfolio")}
        sx={{ alignSelf: "flex-start" }}
      >
        Portfolio
      </Button>
      <Box>
        <Typography variant="h4">{property.name}</Typography>
        <Typography color="text.secondary">
          {property.address_line_1}, {property.suburb}, {property.city}
        </Typography>
      </Box>
      {error && <Alert severity="error">{error}</Alert>}

      <Section
        title="Property components"
        action={
          <Button startIcon={<AddRoundedIcon />} onClick={() => setComponentDialog(true)}>
            Add component
          </Button>
        }
      >
        {components.length === 0 ? (
          <Typography color="text.secondary">No components recorded yet.</Typography>
        ) : (
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", md: "repeat(2, 1fr)" },
              gap: 2,
            }}
          >
            {components.map((component) => (
              <Card key={component.id} variant="outlined">
                <CardContent>
                  <Stack spacing={1.5}>
                    <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>
                        {component.name}
                      </Typography>
                      <Chip size="small" label={component.condition} />
                    </Stack>
                    <Typography color="text.secondary">
                      {categoryName(categories, component.category_code)}
                    </Typography>
                    <Button onClick={() => void openHistory(component)}>
                      View maintenance history
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Box>
        )}
      </Section>

      {selectedComponent && (
        <Section
          title={`${selectedComponent.name} history`}
          action={
            <Button startIcon={<AddRoundedIcon />} onClick={() => setRecordDialog(true)}>
              Add record
            </Button>
          }
        >
          {records.length === 0 ? (
            <Typography color="text.secondary">No maintenance recorded.</Typography>
          ) : (
            <Stack divider={<Divider flexItem />}>
              {records.map((record) => (
                <Stack
                  key={record.id}
                  direction={{ xs: "column", sm: "row" }}
                  sx={{ justifyContent: "space-between", py: 1.5 }}
                >
                  <Box>
                    <Typography sx={{ fontWeight: 700 }}>{record.completed_on}</Typography>
                    <Typography color="text.secondary">
                      {record.notes || "Maintenance completed"}
                    </Typography>
                  </Box>
                  <Typography sx={{ fontWeight: 800 }}>
                    {money.format(Number(record.cost))}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          )}
        </Section>
      )}

      <Section title="Import maintenance CSV">
        <Stack spacing={2}>
          <Typography color="text.secondary">
            Use columns: date, description, amount, and component. Rows are reviewed
            before saving.
          </Typography>
          <Button
            component="label"
            variant="outlined"
            startIcon={<UploadFileRoundedIcon />}
            disabled={busy}
            sx={{ alignSelf: "flex-start" }}
          >
            Choose CSV
            <input
              hidden
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void importFile(file);
              }}
            />
          </Button>
          {preview && (
            <Alert severity={preview.error_count ? "warning" : "success"}>
              {preview.valid_count} valid row(s), {preview.error_count} needing correction.
              <Button
                size="small"
                onClick={() => void confirmImport()}
                disabled={busy || preview.valid_count === 0}
                sx={{ ml: 1 }}
              >
                Confirm valid matched rows
              </Button>
            </Alert>
          )}
        </Stack>
      </Section>

      <Section title="Rule-based maintenance predictions">
        {predictions.length === 0 ? (
          <Typography color="text.secondary">
            Add an installation date or maintenance history to generate predictions.
          </Typography>
        ) : (
          <Stack spacing={2}>
            {predictions.map((prediction) => (
              <Card key={prediction.id} variant="outlined">
                <CardContent>
                  <Stack spacing={1.5}>
                    <Stack direction="row" sx={{ gap: 1, flexWrap: "wrap" }}>
                      <Chip
                        size="small"
                        label={prediction.urgency.replace("_", " ")}
                        color={
                          prediction.urgency === "overdue"
                            ? "error"
                            : prediction.urgency === "due_soon"
                              ? "warning"
                              : "info"
                        }
                      />
                      <Chip size="small" variant="outlined" label={prediction.status} />
                    </Stack>
                    <Typography variant="h6" sx={{ fontWeight: 800 }}>
                      {prediction.component_name}
                    </Typography>
                    <Typography color="text.secondary">
                      Due {prediction.due_date} · Estimated{" "}
                      {money.format(Number(prediction.estimated_cost))}
                    </Typography>
                    <Alert severity="info">
                      <strong>Predefined rule:</strong> {prediction.explanation}
                    </Alert>
                    {(prediction.status === "active" ||
                      prediction.status === "approved") && (
                      <Stack direction="row" spacing={1}>
                        <Button
                          variant="contained"
                          disabled={busy}
                          onClick={() => setPublishing({ kind: "prediction", item: prediction })}
                        >
                          {prediction.status === "active" ? "Approve & publish" : "Publish job"}
                        </Button>
                        {prediction.status === "active" && (
                          <Button disabled={busy} onClick={() => void dismiss(prediction)}>
                            Dismiss
                          </Button>
                        )}
                      </Stack>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Section>

      <Section
        title="Issue report approval queue"
        action={
          <Button startIcon={<AddRoundedIcon />} onClick={() => setReportDialog(true)}>
            Report issue
          </Button>
        }
      >
        {reports.length === 0 ? (
          <Typography color="text.secondary">No issue reports.</Typography>
        ) : (
          <Stack spacing={2}>
            {reports.map((report) => (
              <Card key={report.id} variant="outlined">
                <CardContent>
                  <Stack spacing={1.5}>
                    <Stack direction="row" sx={{ gap: 1, flexWrap: "wrap" }}>
                      <ReportStatusChip status={report.status} />
                      <UrgencyChip urgency={report.urgency} />
                    </Stack>
                    <Typography variant="h6" sx={{ fontWeight: 800 }}>
                      {report.title}
                    </Typography>
                    <Typography color="text.secondary">{report.description}</Typography>
                    <Typography variant="caption">
                      Reported by {report.reporter_name ?? "property member"}
                    </Typography>
                    {report.review_reason && (
                      <Alert severity="info">{report.review_reason}</Alert>
                    )}
                    {report.status === "pending_approval" && (
                      <Stack direction="row" spacing={1}>
                        <Button
                          variant="contained"
                          disabled={busy}
                          onClick={() => setPublishing({ kind: "report", item: report })}
                        >
                          Approve & publish
                        </Button>
                        <Button
                          color="error"
                          disabled={busy}
                          onClick={() => setRejecting(report)}
                        >
                          Reject
                        </Button>
                      </Stack>
                    )}
                    {report.status === "approved" && (
                      <Button
                        variant="contained"
                        disabled={busy}
                        onClick={() => setPublishing({ kind: "report", item: report })}
                      >
                        Publish job
                      </Button>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Section>

      <Section title="Published jobs">
        {jobs.length === 0 ? (
          <Typography color="text.secondary">
            Approved work will appear here after it is published to matching providers.
          </Typography>
        ) : (
          <Stack spacing={2}>
            {jobs.map((job) => (
              <Card key={job.id} variant="outlined">
                <CardContent>
                  <Stack spacing={1}>
                    <Stack direction="row" sx={{ gap: 1, flexWrap: "wrap" }}>
                      <Chip size="small" color="primary" label={job.status} />
                      <Chip size="small" variant="outlined" label={job.category_code} />
                    </Stack>
                    <Typography variant="h6" sx={{ fontWeight: 800 }}>
                      {job.description}
                    </Typography>
                    <Typography color="text.secondary">
                      Budget {money.format(Number(job.budget))} · Public location{" "}
                      {job.public_location}
                    </Typography>
                    {(job.status === "open" || job.status === "awarded") && (
                      <Button
                        variant={job.status === "open" ? "contained" : "outlined"}
                        onClick={() => setReviewingJob(job)}
                        sx={{ alignSelf: "start" }}
                      >
                        {job.status === "open" ? "Review bids" : "View accepted bid"}
                      </Button>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Section>

      <IssueReportDialog
        open={reportDialog}
        propertyId={propertyId}
        categories={categories}
        components={components}
        onClose={() => setReportDialog(false)}
        onCreated={(report) => setReports((current) => [report, ...current])}
      />
      <JobPublishDialog
        open={Boolean(publishing)}
        title={
          publishing?.kind === "prediction"
            ? "Approve predicted maintenance"
            : "Approve reported issue"
        }
        initialDescription={
          publishing?.kind === "report"
            ? publishing.item.description
            : publishing?.kind === "prediction"
              ? `${publishing.item.component_name}: ${publishing.item.explanation}`
              : ""
        }
        initialBudget={
          publishing?.kind === "prediction" ? publishing.item.estimated_cost : "0.00"
        }
        onClose={() => setPublishing(null)}
        onPublish={publish}
      />
      {reviewingJob && (
        <BidReviewDialog
          key={reviewingJob.id}
          job={reviewingJob}
          onClose={() => setReviewingJob(null)}
          onAccepted={async () => {
            const nextJobs = await getPropertyJobs(propertyId);
            setJobs(nextJobs);
            setReviewingJob(
              nextJobs.find((job) => job.id === reviewingJob.id) ?? null,
            );
            setNotice("Bid accepted and job awarded.");
          }}
        />
      )}
      <Snackbar
        open={Boolean(notice)}
        autoHideDuration={5000}
        message={notice}
        onClose={() => setNotice("")}
      />

      <ComponentDialog
        open={componentDialog}
        categories={categories}
        busy={busy}
        onClose={() => setComponentDialog(false)}
        onCreate={async (data) => {
          setBusy(true);
          try {
            const component = await createComponent(propertyId, data);
            setComponents((current) => [...current, component]);
            setComponentDialog(false);
          } finally {
            setBusy(false);
          }
        }}
      />
      <MaintenanceDialog
        open={recordDialog}
        busy={busy}
        onClose={() => setRecordDialog(false)}
        onCreate={async (data) => {
          if (!selectedComponent) return;
          setBusy(true);
          try {
            await createMaintenanceRecord(selectedComponent.id, data);
            await openHistory(selectedComponent);
            setRecordDialog(false);
          } finally {
            setBusy(false);
          }
        }}
      />
      <Dialog open={Boolean(rejecting)} onClose={() => setRejecting(null)} fullWidth>
        <DialogTitle>Reject report</DialogTitle>
        <DialogContent>
          <TextField
            label="Reason"
            value={rejectReason}
            onChange={(event) => setRejectReason(event.target.value)}
            multiline
            minRows={3}
            required
            fullWidth
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejecting(null)}>Cancel</Button>
          <Button
            color="error"
            disabled={busy || rejectReason.trim().length < 3}
            onClick={() => rejecting && void review(rejecting, false, rejectReason)}
          >
            Reject report
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}

function Section({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardContent sx={{ p: { xs: 2.5, md: 3.5 } }}>
        <Stack spacing={2.5}>
          <Stack direction="row" sx={{ justifyContent: "space-between", gap: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              {title}
            </Typography>
            {action}
          </Stack>
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

function ComponentDialog({
  open,
  categories,
  busy,
  onClose,
  onCreate,
}: {
  open: boolean;
  categories: ServiceCategory[];
  busy: boolean;
  onClose: () => void;
  onCreate: (data: {
    category_code: string;
    name: string;
    installed_on?: string;
    condition: ComponentCondition;
  }) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("plumbing");
  const [installedOn, setInstalledOn] = useState("");
  const [condition, setCondition] = useState<ComponentCondition>("unknown");

  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <Stack
        component="form"
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          void onCreate({
            name,
            category_code: category,
            installed_on: installedOn || undefined,
            condition,
          });
        }}
      >
        <DialogTitle>Add component</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <TextField select label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((item) => (
                <MenuItem key={item.code} value={item.code}>{item.name}</MenuItem>
              ))}
            </TextField>
            <TextField label="Installed on" type="date" value={installedOn} onChange={(e) => setInstalledOn(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <TextField select label="Condition" value={condition} onChange={(e) => setCondition(e.target.value as ComponentCondition)}>
              {(["new", "good", "fair", "poor", "unknown"] as const).map((value) => (
                <MenuItem key={value} value={value}>{value}</MenuItem>
              ))}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={busy}>Add component</Button>
        </DialogActions>
      </Stack>
    </Dialog>
  );
}

function MaintenanceDialog({ open, busy, onClose, onCreate }: {
  open: boolean;
  busy: boolean;
  onClose: () => void;
  onCreate: (data: { completed_on: string; cost: string; provider_name?: string; notes?: string }) => Promise<void>;
}) {
  const [completedOn, setCompletedOn] = useState("");
  const [cost, setCost] = useState("");
  const [providerName, setProviderName] = useState("");
  const [notes, setNotes] = useState("");
  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <Stack component="form" onSubmit={(event: FormEvent) => {
        event.preventDefault();
        void onCreate({ completed_on: completedOn, cost, provider_name: providerName || undefined, notes: notes || undefined });
      }}>
        <DialogTitle>Add maintenance record</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField label="Completed on" type="date" value={completedOn} onChange={(e) => setCompletedOn(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} required />
            <TextField label="Cost (ZAR)" type="number" value={cost} onChange={(e) => setCost(e.target.value)} required />
            <TextField label="Provider" value={providerName} onChange={(e) => setProviderName(e.target.value)} />
            <TextField label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} multiline minRows={2} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={busy}>Save record</Button>
        </DialogActions>
      </Stack>
    </Dialog>
  );
}

function categoryName(categories: ServiceCategory[], code: string) {
  return categories.find((category) => category.code === code)?.name ?? code;
}
