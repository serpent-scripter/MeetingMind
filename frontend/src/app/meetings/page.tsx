"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchAPI } from "@/utils/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Meeting } from "@/types";

function formatDuration(seconds?: number) {
  if (seconds == null) return null;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default function MeetingsList() {
  const { token } = useAuth();
  const router = useRouter();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const timeoutId = window.setTimeout(async () => {
      try {
        setLoading(true);
        const query = search.trim()
          ? `/meetings?search=${encodeURIComponent(search.trim())}`
          : "/meetings";
        const data = await fetchAPI(query);
        setMeetings(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [token, router, search]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Meetings</h1>
        <Link href="/dashboard" className="text-blue-600 hover:text-blue-800 font-medium bg-blue-50 px-4 py-2 rounded-md transition-colors">Back to Dashboard</Link>
      </div>
      <input 
        type="text" 
        placeholder="Search title or transcript..." 
        className="w-full border p-2 rounded mb-6 text-gray-900"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div className="space-y-4">
        {loading ? <p className="text-gray-500">Searching meetings...</p> : null}
        {!loading && meetings.length === 0 ? (
          <p className="text-gray-500">
            {search.trim() ? "No meetings matched your search." : "No meetings found."}
          </p>
        ) : null}
        {meetings.map(m => (
          <div key={m.id} className="border p-4 rounded shadow flex justify-between items-center text-gray-900">
            <div>
              <Link href={`/meetings/${m.id}`} className="font-semibold text-lg text-blue-600 hover:underline">{m.title}</Link>
              <div className="flex items-center gap-3 mt-1">
                <p className="text-sm text-gray-500">{new Date(m.recordedAt || m.created_at || "").toLocaleString()}</p>
                {m.duration != null && (
                  <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded border border-gray-200">
                    ⏱ {formatDuration(m.duration)}
                  </span>
                )}
              </div>
              {m.notes ? <p className="mt-2 text-sm text-gray-600">{m.notes}</p> : null}
            </div>
            <span className="text-sm bg-gray-100 px-3 py-1 rounded-full">{m.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
