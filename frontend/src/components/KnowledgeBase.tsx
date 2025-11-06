import { useState, useCallback, useEffect } from "react";
import "./KnowledgeBase.css";

interface KnowledgeStats {
  initialized: boolean;
  total_chunks: number;
  documents_in_db?: number;
  collection_name?: string;
  persist_directory?: string;
}

interface UploadedDocument {
  id: number;
  filename: string;
  file_type: string;
  chunks_count: number;
  source: string;
  uploaded_at: string;
  preview: string;
}

const KnowledgeBase = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<
    "idle" | "uploading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);

  // Fetch knowledge base stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch("http://localhost:8000/api/knowledge/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  // Fetch uploaded documents
  const fetchDocuments = useCallback(async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/knowledge/documents"
      );
      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchDocuments();
  }, [fetchStats, fetchDocuments]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0 && files[0]) {
      await uploadFile(files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0 && files[0]) {
      await uploadFile(files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    // Validate file type
    const validTypes = ["application/pdf", "text/plain"];
    if (!validTypes.includes(file.type)) {
      setUploadStatus("error");
      setMessage("Only PDF and TXT files are supported");
      return;
    }

    setUploadStatus("uploading");
    setMessage("Uploading and processing...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        "http://localhost:8000/api/knowledge/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await response.json();
      setUploadStatus("success");

      let successMsg = `✓ Successfully added "${file.name}" (${data.chunks_created} chunks)`;
      if (data.team_members_created > 0) {
        successMsg += ` · Created ${data.team_members_created} team member${
          data.team_members_created > 1 ? "s" : ""
        }`;
      }

      setMessage(successMsg);

      // Refresh stats and documents list
      await fetchStats();
      await fetchDocuments();

      // Reset after 3 seconds
      setTimeout(() => {
        setUploadStatus("idle");
        setMessage("");
      }, 3000);
    } catch (error: any) {
      setUploadStatus("error");
      setMessage(error.message || "✗ Upload failed. Please try again.");
      console.error("Upload error:", error);

      // Keep error message visible longer
      setTimeout(() => {
        setUploadStatus("idle");
        setMessage("");
      }, 5000);
    }
  };

  const handleClear = async () => {
    if (
      !window.confirm(
        "Are you sure you want to clear the entire knowledge base?"
      )
    ) {
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:8000/api/knowledge/clear",
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Clear failed");
      }

      setMessage("✓ Knowledge base cleared");
      await fetchStats();
      await fetchDocuments();

      setTimeout(() => {
        setMessage("");
      }, 2000);
    } catch (error) {
      setMessage("✗ Failed to clear knowledge base");
      console.error("Clear error:", error);
    }
  };

  return (
    <div className="knowledge-container">
      {/* Header */}
      <div className="knowledge-header">
        <div className="knowledge-header-content">
          <div className="knowledge-led-group">
            <div
              className={`knowledge-led ${
                stats?.initialized ? "knowledge-led-active" : ""
              }`}
            ></div>
            <span className="knowledge-header-title">KNOWLEDGE BASE</span>
          </div>
          <div className="knowledge-header-accent"></div>
        </div>
      </div>

      {/* Stats Panel */}
      <div className="knowledge-stats-panel">
        <div className="knowledge-stat-card">
          <div className="knowledge-stat-icon knowledge-stat-electric">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <div className="knowledge-stat-content">
            <div className="knowledge-stat-value">
              {stats?.total_chunks || 0}
            </div>
            <div className="knowledge-stat-label">Total Chunks</div>
          </div>
        </div>

        <div className="knowledge-stat-card">
          <div className="knowledge-stat-icon knowledge-stat-coral">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
              />
            </svg>
          </div>
          <div className="knowledge-stat-content">
            <div className="knowledge-stat-value">
              {stats?.initialized ? "READY" : "EMPTY"}
            </div>
            <div className="knowledge-stat-label">Status</div>
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="knowledge-upload-section">
        <div className="knowledge-section-header">
          <div className="knowledge-section-stripe"></div>
          <h3 className="knowledge-section-title">UPLOAD DOCUMENT</h3>
        </div>

        <div
          className={`knowledge-dropzone ${
            isDragging ? "knowledge-dropzone-active" : ""
          } ${
            uploadStatus !== "idle" ? `knowledge-dropzone-${uploadStatus}` : ""
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="knowledge-file-input"
            accept=".pdf,.txt"
            onChange={handleFileSelect}
          />

          <div className="knowledge-upload-content">
            {uploadStatus === "uploading" ? (
              <>
                <div className="knowledge-spinner"></div>
                <p className="knowledge-upload-text">{message}</p>
              </>
            ) : uploadStatus === "success" ? (
              <>
                <div className="knowledge-success-icon">✓</div>
                <p className="knowledge-upload-text">{message}</p>
              </>
            ) : uploadStatus === "error" ? (
              <>
                <div className="knowledge-error-icon">✗</div>
                <p className="knowledge-upload-text">{message}</p>
                <label
                  htmlFor="file-upload"
                  className="knowledge-upload-button"
                >
                  Try Again
                </label>
              </>
            ) : (
              <>
                <svg
                  className="knowledge-upload-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="knowledge-upload-text">
                  Drag & drop your PDF or TXT file here
                </p>
                <label
                  htmlFor="file-upload"
                  className="knowledge-upload-button"
                >
                  Or click to browse
                </label>
                <p className="knowledge-upload-hint">
                  <kbd>PDF</kbd> <kbd>TXT</kbd> supported
                </p>
              </>
            )}
          </div>
        </div>

        {message && uploadStatus !== "uploading" && (
          <div
            className={`knowledge-message knowledge-message-${uploadStatus}`}
          >
            {message}
          </div>
        )}
      </div>

      {/* Actions */}
      {stats && stats.total_chunks > 0 && (
        <div className="knowledge-actions">
          <button className="knowledge-clear-button" onClick={handleClear}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            Clear Knowledge Base
          </button>
        </div>
      )}

      {/* Documents List */}
      {documents.length > 0 && (
        <div className="knowledge-documents-section">
          <div className="knowledge-section-header">
            <div className="knowledge-section-stripe"></div>
            <h3 className="knowledge-section-title">UPLOADED DOCUMENTS</h3>
          </div>
          <div className="knowledge-documents-list">
            {documents.map((doc) => (
              <div key={doc.id} className="knowledge-document-card">
                <div className="knowledge-doc-header">
                  <div className="knowledge-doc-icon">
                    {doc.file_type === "pdf" ? "📄" : "📝"}
                  </div>
                  <div className="knowledge-doc-info">
                    <h4 className="knowledge-doc-name">{doc.filename}</h4>
                    <p className="knowledge-doc-meta">
                      {doc.chunks_count} chunks • Uploaded{" "}
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <p className="knowledge-doc-preview">{doc.preview}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Panel */}
      <div className="knowledge-info-panel">
        <div className="knowledge-info-header">
          <div className="knowledge-info-stripe"></div>
          <h4 className="knowledge-info-title">SYSTEM INFO</h4>
        </div>
        <div className="knowledge-info-content">
          <div className="knowledge-info-row">
            <span className="knowledge-info-label">Collection:</span>
            <span className="knowledge-info-value">
              {stats?.collection_name || "team_roles"}
            </span>
          </div>
          <div className="knowledge-info-row">
            <span className="knowledge-info-label">Storage:</span>
            <span className="knowledge-info-value">
              {stats?.persist_directory || "./chroma_db"}
            </span>
          </div>
          <div className="knowledge-info-row">
            <span className="knowledge-info-label">Purpose:</span>
            <span className="knowledge-info-value">
              Documents uploaded here will be used by the AI to make better task
              assignments based on team expertise and roles.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBase;
