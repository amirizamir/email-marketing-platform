"use client";

import { apiFetch } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

type Campaign = {
  id: number;
  name: string;
  status: string;
  sent_count: number;
  failed_count: number;
  total_recipients: number;
};

export default function DashboardPage() {
  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => apiFetch<Campaign[]>("/api/v1/campaigns"),
    refetchInterval: 5000,
  });

  const totals = campaigns.reduce(
    (a, c) => ({
      sent: a.sent + c.sent_count,
      failed: a.failed + c.failed_count,
      pending: a.pending + Math.max(0, c.total_recipients - c.sent_count - c.failed_count),
    }),
    { sent: 0, failed: 0, pending: 0 },
  );

  const pieData = [
    { name: "Sent", value: totals.sent, fill: "#22c55e" },
    { name: "Failed", value: totals.failed, fill: "#ef4444" },
    { name: "Pending", value: totals.pending, fill: "#94a3b8" },
  ].filter((d) => d.value > 0);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">Overview of all campaigns · refreshes every 5s</p>

      <div className="mt-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Sent</div>
          <div className="mt-2 text-3xl font-semibold tabular-nums text-emerald-600">{totals.sent}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Failed</div>
          <div className="mt-2 text-3xl font-semibold tabular-nums text-red-600">{totals.failed}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Pending</div>
          <div className="mt-2 text-3xl font-semibold tabular-nums text-slate-600">{totals.pending}</div>
        </div>
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-slate-900">Distribution</h2>
          <div className="mt-4 h-64">
            {pieData.length === 0 ? (
              <p className="text-sm text-slate-500">No job data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={90} label />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-slate-900">Campaigns</h2>
            <Link
              href="/campaigns/new"
              className="text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              New campaign
            </Link>
          </div>
          <ul className="mt-4 divide-y divide-slate-100">
            {isLoading && <li className="py-3 text-sm text-slate-500">Loading…</li>}
            {!isLoading && campaigns.length === 0 && (
              <li className="py-3 text-sm text-slate-500">No campaigns yet.</li>
            )}
            {campaigns.slice(0, 8).map((c) => (
              <li key={c.id} className="flex items-center justify-between py-3 text-sm">
                <Link href={`/campaigns/${c.id}`} className="font-medium text-slate-800 hover:text-blue-700">
                  {c.name}
                </Link>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  {c.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
