"use client";

import { apiFetch } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

type Template = {
  id: number;
  name: string;
  subject: string;
  html_content: string;
  version: number;
};

export default function EditTemplatePage() {
  const params = useParams();
  const id = Number(params.id);
  const qc = useQueryClient();

  const { data: t } = useQuery({
    queryKey: ["template", id],
    queryFn: () => apiFetch<Template>(`/api/v1/templates/${id}`),
  });

  const [form, setForm] = useState({ name: "", subject: "", html_content: "" });
  useEffect(() => {
    if (t) setForm({ name: t.name, subject: t.subject, html_content: t.html_content });
  }, [t]);

  const save = useMutation({
    mutationFn: () =>
      apiFetch<Template>(`/api/v1/templates/${id}`, {
        method: "PUT",
        body: JSON.stringify(form),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      qc.invalidateQueries({ queryKey: ["template", id] });
    },
  });

  if (!t) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div>
      <Link href="/templates" className="text-sm text-blue-600 hover:underline">
        ← Templates
      </Link>
      <h1 className="mt-4 text-2xl font-semibold text-slate-900">Edit template</h1>
      <p className="text-sm text-slate-500">Version {t.version}</p>

      <div className="mt-6 space-y-3 max-w-2xl">
        <div>
          <label className="text-xs font-medium text-slate-600">Name</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">Subject</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={form.subject}
            onChange={(e) => setForm({ ...form, subject: e.target.value })}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600">HTML</label>
          <textarea
            className="mt-1 w-full min-h-[280px] rounded-md border border-slate-200 px-3 py-2 font-mono text-xs"
            value={form.html_content}
            onChange={(e) => setForm({ ...form, html_content: e.target.value })}
          />
        </div>
        <button
          type="button"
          onClick={() => save.mutate()}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white"
        >
          Save (bumps version)
        </button>
      </div>
    </div>
  );
}
