"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchAPI } from "@/utils/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ActionItemResponse } from "@/types";

export default function ActionsList() {
  const { token } = useAuth();
  const router = useRouter();
  const [actions, setActions] = useState<ActionItemResponse[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDesc, setEditDesc] = useState("");

  const loadActions = () => {
    if (!token) return;
    fetchAPI("/actions?limit=50").then(setActions).catch(console.error);
  };

  useEffect(() => {
    if (!token) router.push("/login");
    else loadActions();
  }, [token, router]);

  const toggleStatus = async (id: string | undefined, current: string) => {
    if (!id) return;
    const nextStatus = current === 'completed' ? 'pending' : 'completed';
    try {
      await fetchAPI(`/actions/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus })
      });
      loadActions();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteAction = async (id: string | undefined) => {
    if (!id) return;
    if (!confirm("Are you sure you want to delete this action item?")) return;
    try {
      await fetchAPI(`/actions/${id}`, { method: "DELETE" });
      loadActions();
    } catch (e) {
      console.error(e);
    }
  };

  const startEdit = (id: string | undefined, desc: string) => {
    if (!id) return;
    setEditingId(id);
    setEditDesc(desc);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditDesc("");
  };

  const saveEdit = async (id: string | undefined) => {
    if (!id || !editDesc.trim()) return;
    try {
      await fetchAPI(`/actions/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ description: editDesc })
      });
      setEditingId(null);
      loadActions();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Action Items</h1>
        <Link href="/dashboard" className="text-blue-600 hover:text-blue-800 font-medium bg-blue-50 px-4 py-2 rounded-md transition-colors">Back to Dashboard</Link>
      </div>
      <div className="space-y-4">
        {actions.map(a => (
          <div key={a.id || a._id} className="border p-4 rounded shadow flex justify-between items-center group">
            <div className="flex items-center gap-3 w-full">
              <input 
                type="checkbox" 
                checked={a.status === 'completed'} 
                onChange={() => toggleStatus(a.id || a._id, a.status)} 
                className="w-5 h-5 flex-shrink-0"
              />
              <div className="flex flex-col flex-1">
                {editingId === (a.id || a._id) ? (
                  <div className="flex flex-col gap-2">
                    <input
                      type="text"
                      value={editDesc}
                      onChange={(e) => setEditDesc(e.target.value)}
                      className="border p-1 rounded text-sm w-full"
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <button onClick={() => saveEdit(a.id || a._id)} className="text-xs bg-blue-500 text-white px-2 py-1 rounded">Save</button>
                      <button onClick={cancelEdit} className="text-xs bg-gray-300 px-2 py-1 rounded">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <span className={a.status === 'completed' ? 'line-through text-gray-500' : ''}>
                      {a.description}
                    </span>
                    {a.assignee && (
                      <span className="text-sm text-blue-600 font-medium mt-1">Assigned to: {a.assignee}</span>
                    )}
                  </>
                )}
              </div>
            </div>
            {editingId !== (a.id || a._id) && (
              <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                <button onClick={() => startEdit(a.id || a._id, a.description)} className="text-blue-500 hover:text-blue-700 text-xl" title="Edit">✏️</button>
                <button onClick={() => deleteAction(a.id || a._id)} className="text-red-500 hover:text-red-700 text-xl" title="Delete">🗑️</button>
              </div>
            )}
          </div>
        ))}
        {actions.length === 0 && <p>No action items found.</p>}
      </div>
    </div>
  );
}
