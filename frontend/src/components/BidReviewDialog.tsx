import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { acceptBid, getJobBids } from "../api/jobs";
import type { Bid, Job } from "../api/types";

const money = new Intl.NumberFormat("en-ZA", {
  style: "currency",
  currency: "ZAR",
});

interface BidReviewDialogProps {
  job: Job;
  onClose: () => void;
  onAccepted: () => Promise<void>;
}

export function BidReviewDialog({ job, onClose, onAccepted }: BidReviewDialogProps) {
  const [bids, setBids] = useState<Bid[]>([]);
  const [confirming, setConfirming] = useState<Bid | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getJobBids(job.id)
      .then(setBids)
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Could not load bids");
      })
      .finally(() => setLoading(false));
  }, [job.id]);

  const accept = async () => {
    if (!confirming) return;
    setBusy(true);
    setError("");
    try {
      await acceptBid(confirming.id);
      setBids(await getJobBids(job.id));
      setConfirming(null);
      await onAccepted();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not accept bid");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Dialog open onClose={busy ? undefined : onClose} fullWidth maxWidth="md">
        <DialogTitle>Compare bids</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800 }}>
                {job.description}
              </Typography>
              <Typography color="text.secondary">
                Budget {money.format(Number(job.budget))} · {job.public_location}
              </Typography>
            </Box>
            {error && <Alert severity="error">{error}</Alert>}
            {loading ? (
              <Stack spacing={1} aria-label="Loading bids">
                <Skeleton variant="rounded" height={130} />
                <Skeleton variant="rounded" height={130} />
              </Stack>
            ) : bids.length === 0 ? (
              <Alert severity="info">
                No providers have bid yet. Leave the job open and check again later.
              </Alert>
            ) : (
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: { xs: "1fr", md: "repeat(2, 1fr)" },
                  gap: 2,
                }}
              >
                {bids.map((bid) => (
                  <Card
                    key={bid.id}
                    variant="outlined"
                    sx={{
                      borderColor: bid.status === "accepted" ? "success.main" : "divider",
                    }}
                  >
                    <CardContent>
                      <Stack spacing={1.5}>
                        <Stack
                          direction="row"
                          sx={{ justifyContent: "space-between", gap: 1 }}
                        >
                          <Typography variant="h6" sx={{ fontWeight: 800 }}>
                            {bid.business_name ?? "Service provider"}
                          </Typography>
                          <Chip
                            size="small"
                            color={bid.status === "accepted" ? "success" : "default"}
                            label={bid.status}
                          />
                        </Stack>
                        <Typography variant="h5" color="primary" sx={{ fontWeight: 900 }}>
                          {money.format(Number(bid.amount))}
                        </Typography>
                        <Typography color="text.secondary">
                          Available {bid.available_on} · Rating {bid.provider_rating ?? "new"}
                        </Typography>
                        <Typography>{bid.message}</Typography>
                        {bid.status === "submitted" && job.status === "open" && (
                          <Button
                            variant="contained"
                            startIcon={<CheckCircleRoundedIcon />}
                            onClick={() => setConfirming(bid)}
                          >
                            Accept bid
                          </Button>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={busy}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(confirming)} onClose={() => setConfirming(null)} maxWidth="xs">
        <DialogTitle>Accept this bid?</DialogTitle>
        <DialogContent>
          <Typography>
            Award {confirming?.business_name ?? "this provider"}{" "}
            {confirming ? money.format(Number(confirming.amount)) : ""}? Competing submitted
            bids will be rejected by the backend.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirming(null)} disabled={busy}>
            Cancel
          </Button>
          <Button variant="contained" onClick={() => void accept()} disabled={busy}>
            {busy ? "Accepting..." : "Confirm award"}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
