"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { fetchAPI } from "@/utils/api";
import Link from "next/link";
import { Meeting } from "@/types";

function formatDuration(seconds?: number) {
  if (seconds == null) return null;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default function Dashboard() {
  const { token, logout, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMeetings = async () => {
    try {
      const meetingsRes = await fetchAPI("/meetings?skip=0&limit=5");
      setMeetings(meetingsRes);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    if (!token) {
      router.push("/login");
      return;
    }

    const fetchData = async () => {
      await fetchMeetings();
      setLoading(false);
    };

    fetchData();
  }, [token, authLoading, router]);

  const handleDelete = async (id: string) => {
    try {
      await fetchAPI(`/meetings/${id}`, { method: 'DELETE' });
      await fetchMeetings();
    } catch (err) {
      console.error('Failed to delete meeting:', err);
    }
  };

  if (!token || loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex flex-wrap items-center gap-4">
          <Link href="/record" className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-md transition-colors">Record Meeting</Link>
          <Link href="/settings" className="text-gray-600 hover:text-gray-900 font-medium px-2 py-2 transition-colors">Settings</Link>
          <button onClick={logout} className="text-red-600 hover:text-red-800 font-medium px-2 py-2 transition-colors">Logout</button>
        </div>
      </div>

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">Recent Meetings</h2>
          {meetings.length > 0 && <Link href="/meetings" className="text-blue-500 text-sm">View All</Link>}
        </div>
        <div className="space-y-4">
          {meetings.length === 0 ? <p className="text-gray-500">No meetings found.</p> : null}
          {meetings.map((m) => (
            <div key={m.id} className="border p-4 rounded shadow-sm flex justify-between items-center">
              <div>
                <Link href={`/meetings/${m.id}`} className="font-medium text-blue-600 hover:underline">{m.title}</Link>
                <div className="flex items-center gap-3 mt-1">
                  <p className="text-sm text-gray-500">{new Date(m.recordedAt || m.created_at || "").toLocaleDateString()}</p>
                  {m.duration != null && (
                    <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded border border-gray-200">
                      ⏱ {formatDuration(m.duration)}
                    </span>
                  )}
                  <span className="text-xs px-2 py-1 bg-gray-100 rounded-full">{m.status}</span>
                </div>
              </div>
              <button 
                onClick={() => handleDelete(m.id)}
                className="text-red-500 hover:text-red-700"
                title="Delete Meeting"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
