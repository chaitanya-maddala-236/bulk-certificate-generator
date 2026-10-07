import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Download, RefreshCw, Send } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const demoPayload = {
  organization_name: "ABC Learning",
  certificate_title: "Certificate of Completion",
  event_name: "Advanced AI Workshop",
  issue_date: "2026-10-07",
  recipients: [
    {
      full_name: "Alice Johnson",
      email: "alice@example.com",
      course_name: "Generative AI",
      external_id: "STU-001"
    },
    {
      full_name: "Bob Smith",
      email: "bob@example.com",
      course_name: "Generative AI",
      external_id: "STU-002"
    },
    {
      full_name: "",
      email: "bad-email",
      course_name: "",
      external_id: "BAD-ROW"
    }
  ]
};

function App() {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [jobDetail, setJobDetail] = useState(null);
  const [recipients, setRecipients] = useState([]);
  const [payload, setPayload] = useState(JSON.stringify(demoPayload, null, 2));
  const [message, setMessage] = useState("");

  const selectedJob = useMemo(
    () => jobs.find((job) => job.job_id === selectedJobId),
    [jobs, selectedJobId]
  );

  async function fetchJobs() {
    const response = await fetch(`${API_BASE}/api/v1/jobs?page_size=20`);
    const data = await response.json();
    setJobs(data.items ?? []);
    if (!selectedJobId && data.items?.length) {
      setSelectedJobId(data.items[0].job_id);
    }
  }

  async function fetchJobDetail(jobId) {
    if (!jobId) return;
    const [jobResponse, recipientsResponse] = await Promise.all([
      fetch(`${API_BASE}/api/v1/jobs/${jobId}`),
      fetch(`${API_BASE}/api/v1/jobs/${jobId}/recipients?page_size=50`)
    ]);
    setJobDetail(await jobResponse.json());
    setRecipients((await recipientsResponse.json()).items ?? []);
  }

  async function submitJob() {
    setMessage("");
    const response = await fetch(`${API_BASE}/api/v1/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error?.message ?? "Request failed");
      return;
    }
    setSelectedJobId(data.job_id);
    setMessage(`Created job ${data.job_id}`);
    await fetchJobs();
    await fetchJobDetail(data.job_id);
  }

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    fetchJobDetail(selectedJobId);
    const interval = setInterval(() => fetchJobDetail(selectedJobId), 3000);
    return () => clearInterval(interval);
  }, [selectedJobId]);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold">Bulk Certificate Generator</h1>
            <p className="text-sm text-slate-500">Demo dashboard for the public API</p>
          </div>
          <button className="icon-button" onClick={fetchJobs} title="Refresh jobs">
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-6">
          <section className="panel">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="section-title">Create Job</h2>
              <button className="primary-button" onClick={submitJob}>
                <Send size={16} />
                Submit
              </button>
            </div>
            <textarea
              className="json-input"
              value={payload}
              onChange={(event) => setPayload(event.target.value)}
            />
            {message ? <p className="mt-3 text-sm text-slate-600">{message}</p> : null}
          </section>

          <section className="panel">
            <h2 className="section-title">Jobs</h2>
            <div className="mt-4 overflow-hidden rounded border border-slate-200">
              {jobs.map((job) => (
                <button
                  key={job.job_id}
                  className={`job-row ${selectedJobId === job.job_id ? "bg-slate-100" : "bg-white"}`}
                  onClick={() => setSelectedJobId(job.job_id)}
                >
                  <span className="font-medium">{job.event_name}</span>
                  <span>{job.status}</span>
                  <span>{job.success_count + job.failure_count + job.invalid_recipients}/{job.total_recipients}</span>
                </button>
              ))}
            </div>
          </section>
        </div>

        <section className="panel">
          <div className="mb-4">
            <h2 className="section-title">{selectedJob?.event_name ?? "Job Detail"}</h2>
            <p className="text-sm text-slate-500">{selectedJobId ?? "Select or create a job"}</p>
          </div>

          {jobDetail ? (
            <>
              <div className="mb-5 grid grid-cols-5 gap-3">
                <Metric label="Total" value={jobDetail.total_recipients} />
                <Metric label="Valid" value={jobDetail.valid_recipients} />
                <Metric label="Success" value={jobDetail.success_count} />
                <Metric label="Failed" value={jobDetail.failure_count} />
                <Metric label="Invalid" value={jobDetail.invalid_recipients} />
              </div>
              <div className="mb-5">
                <div className="mb-2 flex justify-between text-sm">
                  <span>{jobDetail.status}</span>
                  <span>{jobDetail.progress_percent}%</span>
                </div>
                <div className="h-2 rounded bg-slate-200">
                  <div
                    className="h-2 rounded bg-emerald-600"
                    style={{ width: `${jobDetail.progress_percent}%` }}
                  />
                </div>
              </div>
              <div className="overflow-hidden rounded border border-slate-200">
                {recipients.map((recipient) => (
                  <div className="recipient-row" key={recipient.recipient_id}>
                    <div>
                      <p className="font-medium">{recipient.full_name ?? "Invalid recipient"}</p>
                      <p className="text-sm text-slate-500">{recipient.external_id ?? recipient.email}</p>
                    </div>
                    <span>{recipient.status}</span>
                    {recipient.status === "SUCCESS" ? (
                      <a
                        className="icon-button"
                        href={`${API_BASE}/api/v1/jobs/${selectedJobId}/recipients/${recipient.recipient_id}/certificate`}
                        title="Download certificate"
                      >
                        <Download size={16} />
                      </a>
                    ) : (
                      <span className="text-sm text-slate-500">
                        {recipient.error_message ?? recipient.validation_errors?.[0] ?? "-"}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">No job selected.</p>
          )}
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
