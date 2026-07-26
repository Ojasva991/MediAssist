import { useState, useEffect, useCallback, useRef } from "react";
import {
  FileText,
  Upload,
  Download,
  Trash2,
  FlaskConical,
  Scan,
  Pill,
  File as FileIcon,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import { uploadDocument, listDocuments, downloadDocument, deleteDocument } from "@/api/documents";

const CATEGORIES = [
  { value: "BLOOD_TEST", label: "Blood Test", icon: FlaskConical },
  { value: "MRI", label: "MRI", icon: Scan },
  { value: "XRAY", label: "X-Ray", icon: Scan },
  { value: "SONOGRAPHY", label: "Sonography", icon: Scan },
  { value: "PRESCRIPTION", label: "Prescription", icon: Pill },
  { value: "OTHER", label: "Other", icon: FileIcon },
];

const CATEGORY_MAP = Object.fromEntries(CATEGORIES.map((c) => [c.value, c]));

const ACCEPTED_TYPES = "application/pdf,image/jpeg,image/png,image/webp";
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // must match app/storage/document_store.py

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(isoString) {
  try {
    return new Date(isoString).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return isoString;
  }
}

export function DocumentsSection({ userId }) {
  const toast = useToast();
  const fileInputRef = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const [uploadOpen, setUploadOpen] = useState(false);
  const [category, setCategory] = useState("BLOOD_TEST");
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const [downloadingId, setDownloadingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await listDocuments(userId);
      setDocuments(data);
    } catch {
      // Non-fatal - the rest of the Passport page still works without
      // the documents list; just show an empty section.
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  function openUploadDialog() {
    setSelectedFile(null);
    setUploadError(null);
    setCategory("BLOOD_TEST");
    setUploadOpen(true);
  }

  async function handleUpload() {
    if (!selectedFile) {
      setUploadError("Choose a file first.");
      return;
    }
    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setUploadError("File is too large. Maximum is 5 MB.");
      return;
    }
    setIsUploading(true);
    setUploadError(null);
    try {
      const meta = await uploadDocument(userId, selectedFile, category);
      setDocuments((prev) => [meta, ...prev]);
      setUploadOpen(false);
      toast.success("Document uploaded");
    } catch (err) {
      setUploadError(err.message || "Could not upload this file");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDownload(doc) {
    setDownloadingId(doc.id);
    try {
      const blob = await downloadDocument(userId, doc.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = doc.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(err.message || "Could not download this document");
    } finally {
      setDownloadingId(null);
    }
  }

  async function handleDelete(doc) {
    setDeletingId(doc.id);
    try {
      await deleteDocument(userId, doc.id);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
      toast.success("Document deleted");
    } catch (err) {
      toast.error(err.message || "Could not delete this document");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Medical Documents</CardTitle>
        <Button variant="outline" size="sm" onClick={openUploadDialog}>
          <Upload className="size-3.5" /> Upload
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex justify-center py-6 text-ink-faint">
            <Spinner size={18} />
          </div>
        )}

        {!isLoading && documents.length === 0 && (
          <div className="flex flex-col items-center gap-2 rounded-[var(--radius-control)] border border-dashed border-border py-8 text-center">
            <FileText className="size-6 text-ink-faint" />
            <p className="text-sm text-ink-soft">No documents uploaded yet</p>
            <p className="text-xs text-ink-faint">
              Blood tests, MRI, X-ray, sonography, prescriptions - PDF or image, up to 5 MB.
            </p>
          </div>
        )}

        {!isLoading && documents.length > 0 && (
          <ul className="divide-y divide-border">
            {documents.map((doc) => {
              const meta = CATEGORY_MAP[doc.category] ?? CATEGORY_MAP.OTHER;
              const Icon = meta.icon;
              return (
                <li key={doc.id} className="flex items-center gap-3 py-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-[var(--color-mist)] text-ink-soft">
                    <Icon className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{doc.filename}</p>
                    <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
                      <Badge variant="neutral" className="text-[0.65rem]">
                        {meta.label}
                      </Badge>
                      <span className="font-mono text-xs text-ink-faint">
                        {formatFileSize(doc.file_size)} · {formatDate(doc.uploaded_at)}
                      </span>
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownload(doc)}
                      disabled={downloadingId === doc.id}
                      aria-label={`Download ${doc.filename}`}
                    >
                      {downloadingId === doc.id ? <Spinner size={14} /> : <Download className="size-3.5" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(doc)}
                      disabled={deletingId === doc.id}
                      aria-label={`Delete ${doc.filename}`}
                    >
                      {deletingId === doc.id ? <Spinner size={14} /> : <Trash2 className="size-3.5 text-danger" />}
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>

      <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload a document</DialogTitle>
            <DialogDescription>
              PDF or image, up to 5 MB. Tag it with a category so it's easy to find later.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label>Category</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>File</Label>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_TYPES}
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm text-ink-soft file:mr-3 file:rounded-[var(--radius-control)] file:border-0 file:bg-primary-light file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-primary-dark hover:file:bg-primary/20"
              />
              {selectedFile && (
                <p className="text-xs text-ink-faint">{formatFileSize(selectedFile.size)}</p>
              )}
            </div>

            {uploadError && <p className="text-xs text-danger">{uploadError}</p>}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setUploadOpen(false)} disabled={isUploading}>
              Cancel
            </Button>
            <Button onClick={handleUpload} disabled={isUploading}>
              {isUploading ? (
                <>
                  <Spinner size={16} /> Uploading...
                </>
              ) : (
                "Upload"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
