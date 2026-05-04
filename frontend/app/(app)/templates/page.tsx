"use client";

import { apiFetch } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

type Template = {
  id: number;
  name: string;
  subject: string;
  html_content: string;
  version: number;
};

export default function TemplatesPage() {
  const qc = useQueryClient();
  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: () => apiFetch<Template[]>("/api/v1/templates"),
  });

  const [previewId, setPreviewId] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: "Welcome",
    subject: "Hello {{email}}",
    html_content: "<p>Hi {{email}},</p><p>Thanks for being here.</p>",
  });

  const create = useMutation({
    mutationFn: () =>
      apiFetch<Template>("/api/v1/templates", {
        method: "POST",
        body: JSON.stringify(form),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
    },
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Templates</h1>
      <p className="mt-1 text-sm text-slate-500">
        HTML content with variables like <code className="text-xs">{"{{email}}"}</code>
      </p>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-slate-900">New template</h2>
          <div className="mt-4 space-y-3">
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
                className="mt-1 w-full min-h-[200px] rounded-md border border-slate-200 px-3 py-2 font-mono text-xs"
                value={form.html_content}
                onChange={(e) => setForm({ ...form, html_content: e.target.value })}
              />
            </div>
            <button
              type="button"
              onClick={() => create.mutate()}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white"
            >
              Save template
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-slate-900">Your templates</h2>
          <ul className="mt-4 divide-y divide-slate-100">
            {templates.map((t) => (
              <li key={t.id} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <Link href={`/templates/${t.id}`} className="font-medium text-blue-700 hover:underline">
                    {t.name}
                  </Link>
                  <div className="text-xs text-slate-500">v{t.version}</div>
                </div>
                <button
                  type="button"
                  onClick={() => setPreviewId(previewId === t.id ? null : t.id)}
                  className="shrink-0 text-xs font-medium text-slate-600 hover:text-slate-900"
                >
                  {previewId === t.id ? "Hide preview" : "Preview"}
                </button>
              </li>
            ))}
          </ul>
          {previewId !== null && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div
                className="prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{
                  __html: templates.find((x) => x.id === previewId)?.html_content ?? "",
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
