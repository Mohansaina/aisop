"use client";

import { useState, useEffect } from "react";
import { 
  Upload, 
  Trash2, 
  RefreshCw, 
  FileText, 
  Clock, 
  AlertCircle,
  Building,
  CheckCircle2,
  FolderOpen
} from "lucide-react";

interface Document {
  id: string;
  filename: string;
  title: string;
  department: string;
  document_type: string;
  upload_date: string;
  status: "Uploading" | "Processing" | "Indexed" | "Failed";
}

const BACKEND_URL = "http://localhost:8000/api/v1";

export default function DocumentManagerPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [dept, setDept] = useState("Front Office");
  const [docType, setDocType] = useState("SOP");
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);

  // 1. Fetch all documents
  const loadDocuments = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  };

  useEffect(() => {
    loadDocuments();
    // Poll documents status every 5 seconds to update processing progress
    const timer = setInterval(loadDocuments, 5000);
    return () => clearInterval(timer);
  }, []);

  // 2. Handle File Drop / Select
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setUploadFile(e.target.files[0]);
      setMessage(null);
    }
  };

  // 3. Upload File
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsUploading(true);
    setMessage(null);
    setIsError(false);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("department", dept);
    formData.append("document_type", docType);

    try {
      const res = await fetch(`${BACKEND_URL}/documents/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setMessage("File uploaded successfully. Processing has started in the background.");
        setUploadFile(null);
        loadDocuments();
      } else {
        setIsError(true);
        setMessage(data.detail || "Failed to upload file.");
      }
    } catch (err) {
      setIsError(true);
      setMessage("Connection error. Could not connect to backend server.");
    } finally {
      setIsUploading(false);
    }
  };

  // 4. Delete Document
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document? This will remove all associated text chunks and vector embeddings.")) return;
    try {
      const res = await fetch(`${BACKEND_URL}/documents/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        loadDocuments();
      }
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  // 5. Reindex Document
  const handleReindex = async (id: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/documents/${id}/reindex`, {
        method: "POST"
      });
      if (res.ok) {
        loadDocuments();
      }
    } catch (err) {
      console.error("Failed to reindex document:", err);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Indexed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/40 text-emerald-400 border border-emerald-900/30">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Indexed
          </span>
        );
      case "Processing":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-950/40 text-indigo-400 border border-indigo-900/30 animate-pulse">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            Processing
          </span>
        );
      case "Failed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-950/40 text-red-400 border border-red-900/30">
            <AlertCircle className="h-3.5 w-3.5" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-zinc-800 text-zinc-400 border border-zinc-700">
            <Clock className="h-3.5 w-3.5" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="flex-1 p-8 max-w-5xl mx-auto w-full space-y-8">
      {/* Page Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Document Ingestion & Indexing</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Upload manuals and SOPs to the knowledge base or manage existing documents.
        </p>
      </div>

      {/* Grid: Form and Ingested Files */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Card Panel */}
        <div className="bg-zinc-900 border border-zinc-850 rounded-2xl p-6 shadow-xl space-y-5 h-fit">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Upload className="h-5 w-5 text-indigo-400" />
            Index New Document
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            {/* Drag & Drop File Selector */}
            <div className="border border-dashed border-zinc-800 rounded-xl p-6 text-center hover:border-indigo-500/60 transition-colors relative cursor-pointer group bg-zinc-950/20">
              <input 
                type="file" 
                accept=".pdf,.md,.markdown"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center space-y-2">
                <Upload className="h-8 w-8 text-zinc-500 group-hover:text-indigo-400 transition-colors" />
                <p className="text-xs text-zinc-300 font-semibold truncate max-w-full">
                  {uploadFile ? uploadFile.name : "Select or drag file"}
                </p>
                <p className="text-[10px] text-zinc-500">PDF or Markdown (Max 50MB)</p>
              </div>
            </div>

            {/* Department Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-400 flex items-center gap-1.5">
                <Building className="h-3.5 w-3.5" />
                Target Department
              </label>
              <select
                value={dept}
                onChange={(e) => setDept(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-850 rounded-xl px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500"
              >
                {["Front Office", "Culinary / F&B", "Housekeeping", "Maintenance", "Human Resources", "General"].map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            {/* Document Type Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-400 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5" />
                Document Category
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-850 rounded-xl px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500"
              >
                {["SOP", "Policy", "Manual", "Handbook", "Guide"].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            {/* Upload Button */}
            <button
              type="submit"
              disabled={!uploadFile || isUploading}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-xl text-sm font-semibold transition-all cursor-pointer flex items-center justify-center gap-2"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Indexing file...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Ingest Document
                </>
              )}
            </button>
          </form>

          {message && (
            <div className={`
              p-3.5 rounded-xl text-xs flex gap-2
              ${isError 
                ? "bg-red-950/20 border border-red-900/30 text-red-400" 
                : "bg-emerald-950/20 border border-emerald-900/30 text-emerald-400"
              }
            `}>
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{message}</span>
            </div>
          )}
        </div>

        {/* Documents List Panel */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-850 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FolderOpen className="h-5 w-5 text-indigo-400" />
            Ingested Documents ({documents.length})
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-400 font-semibold text-xs uppercase tracking-wider">
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-4">Dept</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-850 text-zinc-300">
                {documents.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-zinc-500">
                      No documents indexed yet. Use the upload panel to seed files.
                    </td>
                  </tr>
                ) : (
                  documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-zinc-850/20 transition-colors">
                      <td className="py-4 px-4 font-semibold text-white">
                        <div className="truncate max-w-[180px]">{doc.title}</div>
                        <div className="text-[10px] text-zinc-500 truncate max-w-[180px]">{doc.filename}</div>
                      </td>
                      <td className="py-4 px-4 text-xs text-zinc-400">{doc.department}</td>
                      <td className="py-4 px-4">
                        <span className="px-2 py-0.5 bg-zinc-850 border border-zinc-800 text-zinc-300 rounded text-[10px] font-bold">
                          {doc.document_type}
                        </span>
                      </td>
                      <td className="py-4 px-4">{getStatusBadge(doc.status)}</td>
                      <td className="py-4 px-4 text-right space-x-1.5">
                        <button
                          onClick={() => handleReindex(doc.id)}
                          title="Reindex embeddings"
                          className="p-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg transition-colors inline-flex cursor-pointer"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          title="Delete document"
                          className="p-1.5 bg-zinc-800/40 hover:bg-red-950/40 text-zinc-500 hover:text-red-400 border border-zinc-800 hover:border-red-900/30 rounded-lg transition-colors inline-flex cursor-pointer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
