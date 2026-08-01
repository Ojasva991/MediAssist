import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { UserPlus, Copy, Check, X, Users, ShieldCheck, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/components/ui/toast";
import {
  createInvite,
  getMyCaregivers,
  getMyPatients,
  revokeCaregiverLink,
  acceptInvite,
} from "@/api/caregivers";
import { ROUTES } from "@/constants/routes";

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function Caregivers() {
  const toast = useToast();

  const [caregivers, setCaregivers] = useState([]);
  const [patients, setPatients] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const [inviteCode, setInviteCode] = useState(null);
  const [inviteExpiresAt, setInviteExpiresAt] = useState(null);
  const [isCreatingInvite, setIsCreatingInvite] = useState(false);
  const [copied, setCopied] = useState(false);

  const [acceptCodeInput, setAcceptCodeInput] = useState("");
  const [isAccepting, setIsAccepting] = useState(false);
  const [acceptError, setAcceptError] = useState(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const [caregiversList, patientsList] = await Promise.all([
        getMyCaregivers(),
        getMyPatients(),
      ]);
      setCaregivers(caregiversList);
      setPatients(patientsList);
    } catch (err) {
      toast.error(err.message || "Couldn't load caregiver info.");
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreateInvite() {
    setIsCreatingInvite(true);
    try {
      const result = await createInvite();
      setInviteCode(result.code);
      setInviteExpiresAt(result.expires_at);
      load();
    } catch (err) {
      toast.error(err.message || "Couldn't create an invite code.");
    } finally {
      setIsCreatingInvite(false);
    }
  }

  function copyCode() {
    navigator.clipboard.writeText(inviteCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleRevoke(linkId) {
    try {
      await revokeCaregiverLink(linkId);
      toast.success("Access revoked");
      load();
    } catch (err) {
      toast.error(err.message || "Couldn't revoke access.");
    }
  }

  async function handleAcceptCode() {
    if (!acceptCodeInput.trim()) return;
    setIsAccepting(true);
    setAcceptError(null);
    try {
      await acceptInvite(acceptCodeInput.trim().toUpperCase());
      toast.success("You now have caregiver access");
      setAcceptCodeInput("");
      load();
    } catch (err) {
      setAcceptError(err.message || "That code didn't work.");
    } finally {
      setIsAccepting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-medium text-ink">Caregivers &amp; Family</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Give a trusted person read-only access to your health info, or manage reminders for
          someone else.
        </p>
      </div>

      <div className="flex items-start gap-2 rounded-[var(--radius-card)] border border-border bg-primary-light p-3 text-xs text-ink-soft">
        <Info className="mt-0.5 size-3.5 shrink-0 text-primary" />
        <p>
          Caregivers get read-only access to your Health Passport and History, plus the ability
          to manage reminders on your behalf. They can't edit your Health Passport itself. You
          can revoke access at any time.
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : (
        <>
          {/* As a patient: invite + manage caregivers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <ShieldCheck className="size-4 text-primary" /> People with access to your account
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {caregivers.length === 0 && (
                <p className="text-sm text-ink-soft">No one has caregiver access yet.</p>
              )}
              {caregivers.map((link) => (
                <div
                  key={link.id}
                  className="flex items-center justify-between border-t border-border pt-3 first:border-t-0 first:pt-0"
                >
                  <div>
                    <p className="text-sm font-medium text-ink">
                      {link.other_party_name || "Pending invite"}
                    </p>
                    <p className="text-xs text-ink-faint">
                      {link.status === "pending"
                        ? `Invited ${formatDate(link.created_at)} - not yet accepted`
                        : `Accepted ${formatDate(link.accepted_at)}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={link.status === "active" ? "success" : "neutral"}>
                      {link.status}
                    </Badge>
                    <Button size="sm" variant="ghost" onClick={() => handleRevoke(link.id)}>
                      <X className="size-3.5 text-danger" />
                    </Button>
                  </div>
                </div>
              ))}

              {inviteCode ? (
                <div className="rounded-[var(--radius-control)] border border-border bg-[var(--color-mist)] p-4">
                  <p className="text-xs text-ink-soft">
                    Share this code with your caregiver. It expires {formatDate(inviteExpiresAt)}.
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <code className="flex-1 rounded-[var(--radius-control)] bg-surface px-3 py-2 text-center font-mono text-lg tracking-widest text-ink">
                      {inviteCode}
                    </code>
                    <Button size="sm" variant="outline" onClick={copyCode}>
                      {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                    </Button>
                  </div>
                </div>
              ) : (
                <Button variant="outline" onClick={handleCreateInvite} disabled={isCreatingInvite}>
                  <UserPlus className="size-4" /> Invite a caregiver
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Accept a code from someone else */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Have an invite code?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                <Input
                  placeholder="e.g. AB3DEF7H"
                  value={acceptCodeInput}
                  onChange={(e) => setAcceptCodeInput(e.target.value)}
                  className="font-mono uppercase"
                />
                <Button onClick={handleAcceptCode} disabled={isAccepting || !acceptCodeInput.trim()}>
                  {isAccepting ? "Linking…" : "Link account"}
                </Button>
              </div>
              {acceptError && <p className="text-sm text-danger">{acceptError}</p>}
            </CardContent>
          </Card>

          {/* As a caregiver: my patients */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Users className="size-4 text-primary" /> People you have access to
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {patients.length === 0 && (
                <p className="text-sm text-ink-soft">
                  You don't have caregiver access to anyone yet.
                </p>
              )}
              {patients.map((link) => (
                <Link
                  key={link.id}
                  to={ROUTES.CAREGIVER_PATIENT.replace(":patientId", link.other_party_user_id)}
                  className="flex items-center justify-between rounded-[var(--radius-control)] border border-border p-3 hover:border-primary hover:bg-primary-light"
                >
                  <div>
                    <p className="text-sm font-medium text-ink">{link.other_party_name}</p>
                    <p className="text-xs text-ink-faint">Since {formatDate(link.accepted_at)}</p>
                  </div>
                  <Badge variant="success">active</Badge>
                </Link>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
