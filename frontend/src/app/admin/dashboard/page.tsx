"use client";

import { useState, useEffect } from "react";
import { 
  BarChart3, 
  Database, 
  Cpu, 
  HardDrive, 
  CheckCircle2, 
  AlertCircle,
  FileText,
  MessageSquare,
  Network
} from "lucide-react";

interface SystemStats {
  documents_indexed: number;
  chunks_stored: number;
  conversations_total: number;
  messages_total: number;
  average_response_time_ms: number;
}

interface SystemStatus {
  database: string;
  vector_database: string;
  llm_provider: string;
  disk_usage_percent: number;
  memory_usage_percent: number;
}

const BACKEND_URL = "http://localhost:8000/api/v1";

export default function SystemStatsPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatsAndHealth = async () => {
    try {
      const [resStats, resStatus] = await Promise.all([
        fetch(`${BACKEND_URL}/system/stats`),
        fetch(`${BACKEND_URL}/system/status`)
      ]);

      if (resStats.ok && resStatus.ok) {
        const statsData = await resStats.json();
        const statusData = await resStatus.json();
        if (statsData.success && statusData.success) {
          setStats(statsData.data);
          setStatus(statusData.data);
        }
      }
    } catch (err) {
      console.error("Failed to load system metrics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatsAndHealth();
    // Poll metrics every 10 seconds
    const interval = setInterval(fetchStatsAndHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusLabel = (val: string) => {
    if (val === "connected" || val === "configured") {
      return (
        <span className="flex items-center gap-1 text-emerald-400 font-semibold text-sm">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          Active / Connected
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 text-red-400 font-semibold text-sm">
        <AlertCircle className="h-4 w-4 text-red-500" />
        Failed / Unconfigured
      </span>
    );
  };

  return (
    <div className="flex-1 p-8 max-w-5xl mx-auto w-full space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">System Monitor & Health</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Real-time resource usage, indexing metrics, and service status of the Operations Assistant.
        </p>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center text-zinc-400">
          Loading metrics...
        </div>
      ) : (
        <>
          {/* Section 1: Ingestion Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Docs card */}
            <div className="bg-zinc-900 border border-zinc-850 p-6 rounded-2xl shadow-xl flex items-center gap-4">
              <div className="p-3 bg-indigo-950/40 text-indigo-400 border border-indigo-900/30 rounded-xl">
                <FileText className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Documents</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {stats?.documents_indexed ?? 0}
                </h3>
              </div>
            </div>

            {/* Chunks card */}
            <div className="bg-zinc-900 border border-zinc-850 p-6 rounded-2xl shadow-xl flex items-center gap-4">
              <div className="p-3 bg-indigo-950/40 text-indigo-400 border border-indigo-900/30 rounded-xl">
                <Network className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Vector Chunks</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {stats?.chunks_stored ?? 0}
                </h3>
              </div>
            </div>

            {/* Conversations card */}
            <div className="bg-zinc-900 border border-zinc-850 p-6 rounded-2xl shadow-xl flex items-center gap-4">
              <div className="p-3 bg-indigo-950/40 text-indigo-400 border border-indigo-900/30 rounded-xl">
                <MessageSquare className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Conversations</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {stats?.conversations_total ?? 0}
                </h3>
              </div>
            </div>

            {/* Latency card */}
            <div className="bg-zinc-900 border border-zinc-850 p-6 rounded-2xl shadow-xl flex items-center gap-4">
              <div className="p-3 bg-indigo-950/40 text-indigo-400 border border-indigo-900/30 rounded-xl">
                <BarChart3 className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Response Time</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {stats?.average_response_time_ms ?? 0} ms
                </h3>
              </div>
            </div>
          </div>

          {/* Section 2: Resource and Connectivity panels */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Services Health */}
            <div className="bg-zinc-900 border border-zinc-850 rounded-2xl p-6 shadow-xl space-y-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-zinc-800 pb-3">
                <Cpu className="h-5 w-5 text-indigo-400" />
                Service Connectivity
              </h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-3.5 bg-zinc-950/40 rounded-xl border border-zinc-850">
                  <span className="text-sm font-semibold text-zinc-300">SQLite Relational Database</span>
                  {getStatusLabel(status?.database ?? "")}
                </div>
                <div className="flex items-center justify-between p-3.5 bg-zinc-950/40 rounded-xl border border-zinc-850">
                  <span className="text-sm font-semibold text-zinc-300">Chroma Vector Storage</span>
                  {getStatusLabel(status?.vector_database ?? "")}
                </div>
                <div className="flex items-center justify-between p-3.5 bg-zinc-950/40 rounded-xl border border-zinc-850">
                  <span className="text-sm font-semibold text-zinc-300">OpenRouter LLM Interface</span>
                  {getStatusLabel(status?.llm_provider ?? "")}
                </div>
              </div>
            </div>

            {/* Hardware Resources */}
            <div className="bg-zinc-900 border border-zinc-850 rounded-2xl p-6 shadow-xl space-y-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-zinc-800 pb-3">
                <HardDrive className="h-5 w-5 text-indigo-400" />
                Host Resource Allocation
              </h2>

              <div className="space-y-5">
                {/* Memory usage */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-zinc-300">Virtual Memory Load</span>
                    <span className="text-indigo-400">{status?.memory_usage_percent ?? 0}%</span>
                  </div>
                  <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                      style={{ width: `${status?.memory_usage_percent ?? 0}%` }}
                      className="h-full bg-indigo-500 transition-all duration-500" 
                    />
                  </div>
                </div>

                {/* Disk usage */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-zinc-300">Disk Partition Capacity</span>
                    <span className="text-indigo-400">{status?.disk_usage_percent ?? 0}%</span>
                  </div>
                  <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                      style={{ width: `${status?.disk_usage_percent ?? 0}%` }}
                      className="h-full bg-indigo-500 transition-all duration-500" 
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
