"use client";

import { apiFetch } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

type Campaign = {
  id: number;
  name: string;
  status: string;
  sent_count: number;
  failed_count: number;
  total_recipients: number;
  created_at: string;
};

export default function CampaignsPage() {
  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => apiFetch<Campaign[]>("/api/v1/campaigns"),
    refetchInterval: 4000,
  });

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Campaigns</h1>
          <p className="mt-1 text-sm text-slate-500">Create, schedule, and monitor sends.</p>
        </div>
        <Link
          href="/campaigns/new"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          New campaign
        </Link>
      </div>

      <div className="mt-8 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Sent</th>
              <th className="px-4 py-3 text-right">Failed</th>
              <th className="px-4 py-3 text-right">Recipients</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {campaigns.map((c) => (
              <tr key={c.id}>
                <td className="px-4 py-3">
                  <Link href={`/campaigns/${c.id}`} className="font-medium text-blue-700 hover:underline">
                    {c.name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">{c.status}</span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">{c.sent_count}</td>
                <td className="px-4 py-3 text-right tabular-nums">{c.failed_count}</td>
                <td className="px-4 py-3 text-right tabular-nums">{c.total_recipients}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
