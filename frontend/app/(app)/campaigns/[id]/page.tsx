"use client";

import { apiFetch } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

type Campaign = {
  id: number;
  name: string;
  status: string;
  sent_count: number;
  failed_count: number;
  total_recipients: number;
  scheduled_at: string | null;
};

type Stats = { sent: number; failed: number; pending: number };

export default function CampaignDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const qc = useQueryClient();

  const { data: campaign } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => apiFetch<Campaign>(`/api/v1/campaigns/${id}`),
    refetchInterval: 3000,
  });

  const { data: stats } = useQuery({
    queryKey: ["campaign-stats", id],
    queryFn: () => apiFetch<Stats>(`/api/v1/campaigns/${id}/stats`),
    refetchInterval: 3000,
  });

  const pause = useMutation({
    mutationFn: () => apiFetch(`/api/v1/campaigns/${id}/pause`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaign", id] });
      qc.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
  const resume = useMutation({
    mutationFn: () => apiFetch(`/api/v1/campaigns/${id}/resume`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaign", id] });
      qc.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
  const retry = useMutation({
    mutationFn: () => apiFetch(`/api/v1/campaigns/${id}/retry-failed`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaign-stats", id] }),
  });

  const pie =
    stats && stats.sent + stats.failed + stats.pending > 0
      ? [
          { name: "Sent", value: stats.sent, fill: "#22c55e" },
          { name: "Failed", value: stats.failed, fill: "#ef4444" },
          { name: "Pending", value: stats.pending, fill: "#94a3b8" },
        ]
      : [];

  if (!campaign) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div>
      <Link href="/campaigns" className="text-sm text-blue-600 hover:underline">
        ← Campaigns
      </Link>
      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{campaign.name}</h1>
          <p className="mt-1 text-sm text-slate-500">
            Status:{" "}
            <span className="font-medium text-slate-800">{campaign.status}</span>
            {campaign.scheduled_at && (
              <span className="ml-2">· Scheduled {new Date(campaign.scheduled_at).toLocaleString()}</span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {campaign.status === "running" && (
            <button
              type="button"
              onClick={() => pause.mutate()}
              className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-900"
            >
              Pause
            </button>
          )}
          {campaign.status === "paused" && (
            <button
              type="button"
              onClick={() => resume.mutate()}
              className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white"
            >
              Resume
            </button>
          )}
          <button
            type="button"
            onClick={() => retry.mutate()}
            className="rounded-md border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700"
          >
            Retry failed
          </button>
        </div>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-medium uppercase text-slate-500">Sent</div>
          <div className="mt-2 text-3xl font-semibold text-emerald-600">{stats?.sent ?? "—"}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-medium uppercase text-slate-500">Failed</div>
          <div className="mt-2 text-3xl font-semibold text-red-600">{stats?.failed ?? "—"}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-medium uppercase text-slate-500">Pending</div>
          <div className="mt-2 text-3xl font-semibold text-slate-600">{stats?.pending ?? "—"}</div>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-medium text-slate-900">Live breakdown</h2>
        <div className="mt-4 h-64">
          {pie.length === 0 ? (
            <p className="text-sm text-slate-500">No jobs yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pie} dataKey="value" nameKey="name" outerRadius={100} label />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
