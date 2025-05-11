"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { fetchAPI } from "@/utils/api";

export default function RecordMeeting() {
  const { token } = useAuth();
  const router = useRouter();
  
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [title, setTitle] = useState("New Meeting");
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = () => {
        setAudioChunks(chunks);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
      setSelectedFile(null); // Clear selected file if recording starts
    } catch (err) {
      console.error("Error accessing microphone", err);
      alert("Microphone access denied or unavailable.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setRecording(false);
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  };

  const saveMeeting = async () => {
    if ((audioChunks.length === 0 && !selectedFile) || !token) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("title", title);
    
    if (selectedFile) {
      formData.append("audioFile", selectedFile);
    } else {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      formData.append("audioFile", audioBlob, "recording.webm");
    }

    try {
      const data = await fetchAPI("/meetings", {
        method: "POST",
        body: formData,
      });
      router.push(`/meetings/${data.id}`);
    } catch (err) {
      console.error(err);
      alert("Error uploading meeting.");
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setAudioChunks([]); // Clear recorded chunks if file selected
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Record or Upload Meeting</h1>
        <Link href="/dashboard" className="text-blue-500 hover:underline">Back to Dashboard</Link>
      </div>

      <div className="bg-white p-6 rounded shadow border">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1 text-gray-700">Meeting Title</label>
          <input 
            type="text" 
            value={title} 
            onChange={(e) => setTitle(e.target.value)} 
            className="w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="mb-6 border-b pb-6">
          <h2 className="text-lg font-semibold mb-3">Record Audio</h2>
          <div className="flex gap-4">
            {!recording ? (
              <button onClick={startRecording} className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded transition-colors">
                Start Recording
              </button>
            ) : (
              <button onClick={stopRecording} className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded animate-pulse">
                Stop Recording
              </button>
            )}
          </div>
          
          {audioChunks.length > 0 && !recording && !selectedFile && (
            <div className="mt-4">
              <audio controls src={URL.createObjectURL(new Blob(audioChunks, { type: "audio/webm" }))} className="mb-4 w-full" />
            </div>
          )}
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-3">Upload Audio File</h2>
          <input 
            type="file" 
            accept="audio/*" 
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
          />
        </div>

        {(audioChunks.length > 0 || selectedFile) && !recording && (
          <div className="mt-6 pt-4 border-t">
            <button 
              onClick={saveMeeting} 
              disabled={uploading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded w-full font-medium disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors"
            >
              {uploading ? "Uploading & Processing..." : "Save Meeting"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
