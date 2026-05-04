"use client";

import { apiFetch } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

type Smtp = {
  id: number;
  name: string;
  smtp_host: string;
  smtp_port: number;
  username: string;
  from_email: string;
  from_name: string;
  use_tls: boolean;
};

export default function SmtpPage() {
  const qc = useQueryClient();
  const { data: accounts = [] } = useQuery({
    queryKey: ["smtp"],
    queryFn: () => apiFetch<Smtp[]>("/api/v1/smtp"),
  });

  const [form, setForm] = useState({
    name: "",
    smtp_host: "",
    smtp_port: 587,
    username: "",
    password: "",
    from_email: "",
    from_name: "",
    use_tls: true,
  });

  const create = useMutation({
    mutationFn: () =>
      apiFetch<Smtp>("/api/v1/smtp", {
        method: "POST",
        body: JSON.stringify(form),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["smtp"] });
      setForm({
        name: "",
        smtp_host: "",
        smtp_port: 587,
        username: "",
        password: "",
        from_email: "",
        from_name: "",
        use_tls: true,
      });
    },
  });

  async function testConnection() {
    await apiFetch("/api/v1/smtp/test", {
      method: "POST",
      body: JSON.stringify({
        smtp_host: form.smtp_host,
        smtp_port: form.smtp_port,
        username: form.username,
        password: form.password,
        use_tls: form.use_tls,
      }),
    });
    alert("SMTP connection OK");
  }

  async function testSaved(id: number) {
    await apiFetch("/api/v1/smtp/test-existing", {
      method: "POST",
      body: JSON.stringify({ smtp_id: id }),
    });
    alert("SMTP connection OK");
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">SMTP senders</h1>
      <p className="mt-1 text-sm text-slate-500">Google Workspace: smtp.gmail.com:587, TLS on.</p>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-slate-900">Add account</h2>
          <div className="mt-4 grid gap-3">
            {(
              [
                ["name", "Name"],
                ["smtp_host", "Host"],
                ["smtp_port", "Port"],
                ["username", "Username"],
                ["password", "Password"],
                ["from_email", "From email"],
                ["from_name", "From name"],
              ] as const
            ).map(([k, label]) => (
              <div key={k}>
                <label className="text-xs font-medium text-slate-600">{label}</label>
                <input
                  className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                  type={k === "password" ? "password" : k === "smtp_port" ? "number" : "text"}
                  value={form[k] as string | number}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      [k]: k === "smtp_port" ? Number(e.target.value) : e.target.value,
                    })
                  }
                />
              </div>
            ))}
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.use_tls}
                onChange={(e) => setForm({ ...form, use_tls: e.target.checked })}
              />
              Use TLS (STARTTLS)
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => testConnection()}
                className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Test connection
              </button>
              <button
                type="button"
                onClick={() => create.mutate()}
                disabled={create.isPending}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-medium text-slate-900">Saved accounts</h2>
          <ul className="mt-4 divide-y divide-slate-100">
            {accounts.map((a) => (
              <li key={a.id} className="flex items-center justify-between py-3 text-sm">
                <div>
                  <div className="font-medium text-slate-900">{a.name}</div>
                  <div className="text-xs text-slate-500">
                    {a.smtp_host}:{a.smtp_port} · {a.from_email}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => testSaved(a.id)}
                  className="rounded-md border border-slate-200 px-3 py-1 text-xs font-medium hover:bg-slate-50"
                >
                  Test
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
