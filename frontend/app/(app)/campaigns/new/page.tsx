"use client";

import { apiFetch } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

type Opt = { id: number; name?: string; subject?: string };

export default function NewCampaignPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [name, setName] = useState("Newsletter");
  const [senderId, setSenderId] = useState<number | "">("");
  const [templateId, setTemplateId] = useState<number | "">("");
  const [listId, setListId] = useState<number | "">("");
  const [scheduleAt, setScheduleAt] = useState("");
  const [mode, setMode] = useState<"now" | "schedule">("now");

  const { data: smtp = [] } = useQuery({
    queryKey: ["smtp"],
    queryFn: () => apiFetch<Opt[]>("/api/v1/smtp"),
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: () => apiFetch<Opt[]>("/api/v1/templates"),
  });
  const { data: lists = [] } = useQuery({
    queryKey: ["lists"],
    queryFn: () => apiFetch<Opt[]>("/api/v1/lists"),
  });

  async function submit() {
    if (!senderId || !templateId || !listId) return;
    const camp = await apiFetch<{ id: number }>("/api/v1/campaigns", {
      method: "POST",
      body: JSON.stringify({
        name,
        template_id: templateId,
        sender_id: senderId,
        list_id: listId,
      }),
    });
    if (mode === "schedule" && scheduleAt) {
      const iso = new Date(scheduleAt).toISOString();
      await apiFetch(`/api/v1/campaigns/${camp.id}/schedule`, {
        method: "POST",
        body: JSON.stringify({ scheduled_at: iso }),
      });
    } else {
      await apiFetch(`/api/v1/campaigns/${camp.id}/start`, { method: "POST" });
    }
    router.push(`/campaigns/${camp.id}`);
  }

  return (
    <div>
      <Link href="/campaigns" className="text-sm text-blue-600 hover:underline">
        ← Campaigns
      </Link>
      <h1 className="mt-4 text-2xl font-semibold text-slate-900">New campaign</h1>
      <div className="mt-2 flex gap-2 text-xs">
        {[1, 2, 3].map((s) => (
          <span
            key={s}
            className={`rounded-full px-2 py-0.5 ${step === s ? "bg-blue-100 text-blue-800" : "bg-slate-100 text-slate-600"}`}
          >
            Step {s}
          </span>
        ))}
      </div>

      <div className="mt-8 max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="font-medium text-slate-900">Basics</h2>
            <div>
              <label className="text-xs text-slate-600">Campaign name</label>
              <input
                className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <button
              type="button"
              onClick={() => setStep(2)}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white"
            >
              Next
            </button>
          </div>
        )}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="font-medium text-slate-900">Sender & template</h2>
            <div>
              <label className="text-xs text-slate-600">SMTP account</label>
              <select
                className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                value={senderId === "" ? "" : senderId}
                onChange={(e) => setSenderId(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">Select…</option>
                {smtp.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name ?? s.id}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-600">Template</label>
              <select
                className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                value={templateId === "" ? "" : templateId}
                onChange={(e) => setTemplateId(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">Select…</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {(t.name ?? "") + (t.subject ? ` — ${t.subject}` : "")}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => setStep(1)} className="text-sm text-slate-600">
                Back
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white"
              >
                Next
              </button>
            </div>
          </div>
        )}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="font-medium text-slate-900">Audience & launch</h2>
            <div>
              <label className="text-xs text-slate-600">Contact list</label>
              <select
                className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                value={listId === "" ? "" : listId}
                onChange={(e) => setListId(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">Select…</option>
                {lists.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  checked={mode === "now"}
                  onChange={() => setMode("now")}
                />
                Send now
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  checked={mode === "schedule"}
                  onChange={() => setMode("schedule")}
                />
                Schedule
              </label>
            </div>
            {mode === "schedule" && (
              <input
                type="datetime-local"
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                value={scheduleAt}
                onChange={(e) => setScheduleAt(e.target.value)}
              />
            )}
            <div className="flex gap-2">
              <button type="button" onClick={() => setStep(2)} className="text-sm text-slate-600">
                Back
              </button>
              <button
                type="button"
                onClick={() => submit()}
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
              >
                {mode === "schedule" ? "Schedule" : "Start"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
