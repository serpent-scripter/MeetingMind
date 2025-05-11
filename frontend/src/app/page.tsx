"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function Home() {
  const { user, isLoading } = useAuth();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center bg-white">
      <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl mb-6">
        MeetingMind
      </h1>
      <p className="text-lg leading-8 text-gray-600 mb-8 max-w-2xl">
        AI-powered meeting assistant to transcribe, summarize, and extract action items from your meetings automatically.
      </p>
      
      {!isLoading && (
        <div className="flex gap-4">
          {user ? (
            <Link 
              href="/dashboard"
              className="px-6 py-3 text-white bg-blue-600 rounded-md hover:bg-blue-700 font-semibold"
            >
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link 
                href="/login"
                className="px-6 py-3 text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 font-semibold"
              >
                Log in
              </Link>
              <Link 
                href="/signup"
                className="px-6 py-3 text-white bg-blue-600 rounded-md hover:bg-blue-700 font-semibold"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      )}
    </div>
  );
}
