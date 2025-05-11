"use client";

import { useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchAPI } from "@/utils/api";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Settings() {
  const { token, user, logout } = useAuth();
  const router = useRouter();
  const nameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!token) router.push("/login");
  }, [token, router]);

  const updateProfile = async () => {
    try {
      const nextName = nameInputRef.current?.value || "";
      await fetchAPI("/users/me", {
        method: "PATCH",
        body: JSON.stringify({ name: nextName })
      });
      alert("Profile updated successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to update profile.");
    }
  };

  const deleteAccount = async () => {
    if (!confirm("Are you sure you want to delete your account? This cannot be undone.")) return;
    try {
      await fetchAPI("/users/me", { method: "DELETE" });
      logout();
    } catch (err) {
      console.error(err);
      alert("Failed to delete account.");
    }
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Settings</h1>
        <Link href="/dashboard" className="text-blue-500">Back</Link>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input type="text" value={user?.email || ""} disabled className="w-full border p-2 rounded bg-gray-100" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Name</label>
          <input ref={nameInputRef} type="text" defaultValue={user?.name || ""} className="w-full border p-2 rounded" />
        </div>
        <button onClick={updateProfile} className="w-full bg-blue-500 text-white p-2 rounded">
          Update Profile
        </button>
        <hr />
        <button onClick={deleteAccount} className="w-full bg-red-600 text-white p-2 rounded">
          Delete Account
        </button>
      </div>
    </div>
  );
}
