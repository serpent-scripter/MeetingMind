"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { fetchAPI, API_BASE_URL, BACKEND_URL } from "@/utils/api";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { MeetingDetailResponse, ActionItemResponse } from "@/types";

export default function MeetingDetail() {
  const { id } = useParams();
  const { token } = useAuth();
  const router = useRouter();
  
  const [meeting, setMeeting] = useState<MeetingDetailResponse | null>(null);
  const [actions, setActions] = useState<ActionItemResponse[]>([]);
  const [newAction, setNewAction] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [editableTitle, setEditableTitle] = useState("");
  const [editableNotes, setEditableNotes] = useState("");
  const [savingMeeting, setSavingMeeting] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<"txt" | "json" | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDesc, setEditDesc] = useState("");

  const fetchDetails = useCallback(async () => {
    if (!token) return;
    try {
      const m = await fetchAPI(`/meetings/${id}`);
      setMeeting(m);
      setActions(m.actionItems || []);
      setEditableTitle(m.title || "");
      setEditableNotes(m.notes || "");
    } catch (e) {
      console.error(e);
    }
  }, [id, token]);

  useEffect(() => {
    if (!token) router.push("/login");
    fetchDetails();

    const interval = setInterval(() => {
      if (meeting?.status !== "completed" && meeting?.status !== "failed" && meeting?.status !== "error") {
        fetchDetails();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [token, router, meeting?.status, fetchDetails]);

  const addAction = async () => {
    if (!newAction.trim()) return;
    setErrorMsg("");
    try {
      await fetchAPI("/actions", {
        method: "POST",
        body: JSON.stringify({
          meetingId: id,
          description: newAction,
          status: "pending"
        })
      });
      setNewAction("");
      fetchDetails();
    } catch (e: unknown) {
      console.error(e);
      if (e instanceof Error) {
        setErrorMsg(e.message);
      } else if (typeof e === "string") {
        setErrorMsg(e);
      } else {
        setErrorMsg("Failed to add action item");
      }
    }
  };

  const toggleAction = async (actionId: string | undefined, currentStatus: string) => {
    if (!actionId) return;
    const nextStatus = currentStatus === 'completed' ? 'pending' : 'completed';
    try {
      await fetchAPI(`/actions/${actionId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus })
      });
      fetchDetails();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteAction = async (actionId: string | undefined) => {
    if (!actionId) return;
    if (!confirm("Are you sure you want to delete this action item?")) return;
    try {
      await fetchAPI(`/actions/${actionId}`, { method: "DELETE" });
      fetchDetails();
    } catch (e) {
      console.error(e);
    }
  };

  const startEdit = (actionId: string | undefined, desc: string) => {
    if (!actionId) return;
    setEditingId(actionId);
    setEditDesc(desc);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditDesc("");
  };

  const saveEdit = async (actionId: string | undefined) => {
    if (!actionId || !editDesc.trim()) return;
    try {
      await fetchAPI(`/actions/${actionId}`, {
        method: "PATCH",
        body: JSON.stringify({ description: editDesc })
      });
      setEditingId(null);
      fetchDetails();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteMeeting = async () => {
    if (!confirm("Are you sure you want to delete this meeting?")) return;
    try {
      await fetchAPI(`/meetings/${id}`, { method: "DELETE" });
      router.push("/dashboard");
    } catch (e) {
      console.error(e);
    }
  };

  const saveMeetingDetails = async () => {
    if (!meeting) return;
    setErrorMsg("");
    setSavingMeeting(true);
    try {
      const updatedMeeting = await fetchAPI(`/meetings/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          title: editableTitle,
          notes: editableNotes,
        }),
      });
      setMeeting((prev) =>
        prev
          ? {
              ...prev,
              ...updatedMeeting,
              notes: editableNotes,
            }
          : prev
      );
    } catch (e: unknown) {
      console.error(e);
      setErrorMsg(e instanceof Error ? e.message : "Failed to save meeting details");
    } finally {
      setSavingMeeting(false);
    }
  };

  const exportTranscript = async (format: "txt" | "json") => {
    if (!token) return;
    setErrorMsg("");
    setExportingFormat(format);
    try {
      const response = await fetch(
        `${API_BASE_URL}/meetings/${id}/transcript/export?format=${format}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        let errorMessage = "Failed to export transcript";
        try {
          const errorData = await response.json();
          if (errorData.detail) errorMessage = errorData.detail;
        } catch {
          // Ignore JSON parse errors and keep default message.
        }
        throw new Error(errorMessage);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const contentDisposition = response.headers.get("Content-Disposition");
      const filenameMatch = contentDisposition?.match(/filename="([^"]+)"/);
      link.href = downloadUrl;
      link.download = filenameMatch?.[1] || `meeting_transcript.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (e: unknown) {
      console.error(e);
      setErrorMsg(e instanceof Error ? e.message : "Failed to export transcript");
    } finally {
      setExportingFormat(null);
    }
  };

  if (!meeting) return <div className="p-6">Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-600 mb-2">Meeting Title</label>
          <input
            type="text"
            value={editableTitle}
            onChange={(e) => setEditableTitle(e.target.value)}
            className="w-full rounded border p-3 text-3xl font-bold"
          />
        </div>
        <div className="flex items-center gap-4">
          <button onClick={deleteMeeting} className="text-red-600 border border-red-600 px-3 py-1 rounded hover:bg-red-50 text-sm font-medium">
            Delete Meeting
          </button>
          <Link href="/dashboard" className="text-blue-500">Back to Dashboard</Link>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="px-3 py-1 bg-gray-200 rounded-full text-sm font-medium">{meeting.status}</span>
        <span className="text-gray-500 text-sm">{new Date(meeting.recordedAt || meeting.created_at || "").toLocaleString()}</span>
        <button
          onClick={saveMeetingDetails}
          disabled={savingMeeting}
          className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white disabled:bg-blue-300"
        >
          {savingMeeting ? "Saving..." : "Save Details"}
        </button>
      </div>
      {errorMsg && <p className="text-red-500 text-sm">{errorMsg}</p>}

      {(meeting.audioFilePath || meeting.audio_url) && (
        <div className="bg-white p-4 border rounded shadow-sm mb-6">
          <h2 className="text-xl font-semibold mb-2">Recording</h2>
          <audio 
            controls 
            src={`${BACKEND_URL}${meeting.audioFilePath || meeting.audio_url}`} 
            className="w-full rounded-lg outline-none" 
          />
        </div>
      )}

      <div className="bg-white p-4 border rounded shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-semibold">Notes</h2>
          <div className="flex gap-2">
            <button
              onClick={() => exportTranscript("txt")}
              disabled={!meeting.transcript?.content || exportingFormat !== null}
              className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              {exportingFormat === "txt" ? "Exporting TXT..." : "Export TXT"}
            </button>
            <button
              onClick={() => exportTranscript("json")}
              disabled={!meeting.transcript?.content || exportingFormat !== null}
              className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              {exportingFormat === "json" ? "Exporting JSON..." : "Export JSON"}
            </button>
          </div>
        </div>
        <textarea
          value={editableNotes}
          onChange={(e) => setEditableNotes(e.target.value)}
          placeholder="Add meeting notes here..."
          className="min-h-36 w-full rounded border p-3 text-sm text-gray-800"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div className="bg-white p-4 border rounded shadow-sm">
            <h2 className="text-xl font-semibold mb-2">Summary</h2>
            <div className="text-gray-700 prose max-w-none max-h-96 overflow-y-auto">
              {meeting.summary?.summaryText ? (
                <ReactMarkdown>{meeting.summary.summaryText}</ReactMarkdown>
              ) : (
                <p>Summary not available yet.</p>
              )}
            </div>
          </div>

          <div className="bg-white p-4 border rounded shadow-sm">
            <h2 className="text-xl font-semibold mb-2">Transcript</h2>
            <div className="h-64 overflow-y-auto text-sm text-gray-700 bg-gray-50 p-2 rounded">
              {meeting.transcript?.timestampedSegments ? (
                <div className="space-y-2">
                  {meeting.transcript.timestampedSegments.map((seg: { speaker?: string; text: string }, idx: number) => (
                    <p key={idx}>
                      {seg.speaker && <span className="font-bold mr-1">{seg.speaker}:</span>}
                      {seg.text}
                    </p>
                  ))}
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{meeting.transcript?.content || "Transcript not available yet."}</p>
              )}
            </div>
          </div>
        </div>

        <div>
          <div className="bg-white p-4 border rounded shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Action Items</h2>
            <div className="flex gap-2 mb-4">
              <input 
                type="text" 
                value={newAction} 
                onChange={(e) => setNewAction(e.target.value)}
                placeholder="New action item..." 
                className="flex-1 border p-2 rounded text-sm"
              />
              <button 
                onClick={addAction} 
                disabled={!newAction.trim()}
                className="bg-blue-500 text-white px-4 py-2 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add
              </button>
            </div>
            <div className="space-y-2">
              {actions.map(a => (
                <div key={a.id || a._id} className="flex items-start gap-2 p-2 border-b group">
                  <input 
                    type="checkbox" 
                    checked={a.status === 'completed'}
                    onChange={() => toggleAction(a.id || a._id, a.status)}
                    className="mt-1"
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
                        <span className={`text-sm ${a.status === 'completed' ? 'line-through text-gray-400' : ''}`}>
                          {a.description}
                        </span>
                        {a.assignee && (
                          <span className="text-xs text-blue-600 font-medium mt-1">Assigned to: {a.assignee}</span>
                        )}
                      </>
                    )}
                  </div>
                  {editingId !== (a.id || a._id) && (
                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => startEdit(a.id || a._id, a.description)} className="text-blue-500 text-sm" title="Edit">✏️</button>
                      <button onClick={() => deleteAction(a.id || a._id)} className="text-red-500 text-sm" title="Delete">🗑️</button>
                    </div>
                  )}
                </div>
              ))}
              {actions.length === 0 && <p className="text-sm text-gray-500">No action items yet.</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
