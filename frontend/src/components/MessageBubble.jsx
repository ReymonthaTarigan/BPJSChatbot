export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"} animate-[fadeIn_0.25s_ease-out]`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-teal-900 text-white text-[11px] font-display font-bold flex items-center justify-center shrink-0 mr-2 mt-0.5">
          J
        </div>
      )}

      <div
        className={`max-w-[78%] px-4 py-3 text-[14px] leading-relaxed ${
          isUser
            ? "bg-teal-900 text-white rounded-2xl rounded-tr-sm"
            : "bg-teal-100/50 text-teal-950 rounded-2xl rounded-tl-sm border border-teal-900/10"
        }`}
      >
        <div className="whitespace-pre-wrap">{message.text}</div>

        {!isUser && message.sources?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-teal-900/10 space-y-1.5">
            <div className="text-[10px] uppercase tracking-wide font-semibold text-teal-900/50">
              Sumber panduan
            </div>
            {message.sources.map((source, idx) => (
              <a
                key={idx}
                href={source.sumber_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-[12.5px] text-teal-800 hover:text-clay-600 group transition-colors"
              >
                <span className="w-1 h-1 rounded-full bg-teal-800/40 group-hover:bg-clay-600 shrink-0" />
                <span className="underline decoration-teal-800/20 underline-offset-2 group-hover:decoration-clay-600">
                  {source.judul}
                </span>
              </a>
            ))}
          </div>
        )}

        {!isUser && message.groundednessStatus && (
          <div className="mt-3 flex items-center gap-2">
            <GroundednessBadge status={message.groundednessStatus} />
            {message.confidence !== undefined && (
              <span className="text-[11px] text-teal-900/40">
                {(message.confidence * 100).toFixed(0)}% kecocokan
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function GroundednessBadge({ status }) {
  const isVerified = status.startsWith("YA");

  return (
    <span
      className={`inline-flex items-center gap-1 text-[10.5px] px-2 py-0.5 rounded-full font-medium ${
        isVerified
          ? "bg-teal-900/10 text-teal-900"
          : "bg-clay-100 text-clay-600"
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${isVerified ? "bg-teal-800" : "bg-clay-600"}`} />
      {isVerified ? "Terverifikasi" : "Perlu dicek manual"}
    </span>
  );
}