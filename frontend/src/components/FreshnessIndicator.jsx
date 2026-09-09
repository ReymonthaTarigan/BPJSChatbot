import { useState, useEffect } from "react";
import { getStatus, triggerUpdate } from "../api/client";

export default function FreshnessIndicator() {
  const [status, setStatus] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState("");

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    try {
      const data = await getStatus();
      setStatus(data);
    } catch (error) {
      console.error("Gagal ambil status:", error);
    }
  }

  async function handleUpdateClick() {
    setIsUpdating(true);
    setUpdateMessage("");
    try {
      const result = await triggerUpdate();
      setUpdateMessage(result.message);
      await loadStatus();
    } catch (error) {
      setUpdateMessage("Gagal melakukan update data.");
    } finally {
      setIsUpdating(false);
    }
  }

  if (!status) return null;

  return (
    <div className="flex items-center justify-between px-6 py-2.5 bg-teal-100/60 border-b border-teal-900/10 text-xs text-teal-900/70">
      <div className="flex items-center gap-3">
        <span className="font-medium">{status.total_chunks} panduan</span>
        <span className="w-1 h-1 rounded-full bg-teal-900/30" />
        <span>{status.categories.length} kategori</span>
        {updateMessage && (
          <>
            <span className="w-1 h-1 rounded-full bg-teal-900/30" />
            <span className="text-teal-800">{updateMessage}</span>
          </>
        )}
      </div>

      <button
        onClick={handleUpdateClick}
        disabled={isUpdating}
        className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white text-teal-900 font-medium border border-teal-900/15 hover:border-teal-900/30 hover:bg-teal-50 disabled:opacity-50 transition-colors"
      >
        <svg
          className={`w-3 h-3 ${isUpdating ? "animate-spin" : ""}`}
          viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
        >
          <path d="M3 12a9 9 0 0 1 15-6.7L21 8" strokeLinecap="round" />
          <path d="M21 3v5h-5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M21 12a9 9 0 0 1-15 6.7L3 16" strokeLinecap="round" />
          <path d="M3 21v-5h5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {isUpdating ? "Memeriksa..." : "Perbarui data"}
      </button>
    </div>
  );
}