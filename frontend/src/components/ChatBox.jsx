import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../api/client";
import MessageBubble from "./MessageBubble";

export default function ChatBox() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Halo! Saya asisten panduan Mobile JKN. Tanyakan apa saja seputar pendaftaran, akun, pelayanan, atau iuran kepesertaan — jawaban saya bersumber langsung dari panduan resmi BPJS Kesehatan.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSend() {
    const question = input.trim();
    if (!question || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setIsLoading(true);

    try {
      const result = await sendChatMessage(question);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: result.answer,
          sources: result.sources,
          confidence: result.confidence,
          groundednessStatus: result.groundedness_status,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Maaf, terjadi kesalahan saat menghubungi server. Coba lagi sebentar lagi." },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const suggestions = [
    "Bagaimana cara mendaftar sebagai peserta JKN?",
    "Bagaimana cara mengubah data alamat?",
    "Bagaimana cara mengambil antrean di puskesmas?",
  ];

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex-1 overflow-y-auto px-5 py-5">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}

        {messages.length === 1 && (
          <div className="flex flex-col gap-2 mt-2 ml-9">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => setInput(s)}
                className="text-left text-[13px] text-teal-800 bg-white border border-teal-900/15 rounded-xl px-3.5 py-2.5 hover:border-clay-600 hover:text-clay-600 transition-colors w-fit"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {isLoading && (
          <div className="flex items-center gap-1.5 ml-9 mt-1">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-900/30 animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-teal-900/30 animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-teal-900/30 animate-bounce" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="flex items-end gap-2 px-5 py-4 border-t border-teal-900/10 bg-white">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tulis pertanyaan Anda..."
          rows={1}
          className="flex-1 px-4 py-2.5 rounded-xl border border-teal-900/15 text-[14px] resize-none focus:outline-none focus:ring-2 focus:ring-clay-600/40 focus:border-clay-600/50 placeholder:text-teal-900/35"
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="w-10 h-10 shrink-0 rounded-xl bg-teal-900 text-white flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed hover:bg-teal-800 transition-colors"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M22 2 11 13" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M22 2 15 22l-4-9-9-4 20-7Z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </div>
  );
}