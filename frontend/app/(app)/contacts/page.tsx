"use client";

import { apiFetch, apiUrl } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

type List = { id: number; name: string };
type Contact = { id: number; email: string; list_id: number };

export default function ContactsPage() {
  const qc = useQueryClient();
  const [listId, setListId] = useState<number | "">("");

  const { data: lists = [] } = useQuery({
    queryKey: ["lists"],
    queryFn: () => apiFetch<List[]>("/api/v1/lists"),
  });

  const { data: contacts = [] } = useQuery({
    queryKey: ["contacts", listId],
    queryFn: () =>
      apiFetch<Contact[]>(
        listId === "" ? "/api/v1/contacts?limit=200" : `/api/v1/contacts?list_id=${listId}&limit=200`,
      ),
    enabled: lists.length > 0,
  });

  const [newListName, setNewListName] = useState("");
  const createList = useMutation({
    mutationFn: () =>
      apiFetch<List>("/api/v1/lists", {
        method: "POST",
        body: JSON.stringify({ name: newListName }),
      }),
    onSuccess: (l) => {
      qc.invalidateQueries({ queryKey: ["lists"] });
      setListId(l.id);
      setNewListName("");
    },
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("list_id", String(listId));
      const t = localStorage.getItem("emp_token");
      const res = await fetch(apiUrl("/api/v1/contacts/upload"), {
        method: "POST",
        headers: t ? { Authorization: `Bearer ${t}` } : {},
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["contacts"] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Contacts</h1>
      <p className="mt-1 text-sm text-slate-500">
        Upload CSV with one column: email (header optional).
      </p>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-medium text-slate-900">Lists</h2>
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs font-medium text-slate-600">Active list</label>
            <select
              className="mt-1 block rounded-md border border-slate-200 px-3 py-2 text-sm"
              value={listId === "" ? "" : listId}
              onChange={(e) => setListId(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">All contacts</option>
              {lists.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <input
              placeholder="New list name"
              className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              value={newListName}
              onChange={(e) => setNewListName(e.target.value)}
            />
            <button
              type="button"
              onClick={() => newListName && createList.mutate()}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            >
              Create list
            </button>
          </div>
        </div>

        {listId !== "" && (
          <div className="mt-6">
            <label className="text-xs font-medium text-slate-600">Upload CSV</label>
            <input
              type="file"
              accept=".csv,text/csv"
              className="mt-2 block text-sm"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload.mutate(f);
              }}
            />
            {upload.isSuccess && (
              <p className="mt-2 text-xs text-emerald-700">Upload processed.</p>
            )}
          </div>
        )}
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">List</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {contacts.map((c) => (
              <tr key={c.id}>
                <td className="px-4 py-2 font-mono text-slate-800">{c.email}</td>
                <td className="px-4 py-2 text-slate-600">{c.list_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
