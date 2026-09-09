import FreshnessIndicator from "./components/FreshnessIndicator";
import ChatBox from "./components/ChatBox";

function App() {
  return (
    <div className="min-h-screen bg-cream flex items-center justify-center p-4">
      <div className="w-full max-w-2xl h-[90vh] bg-white rounded-2xl shadow-xl shadow-teal-950/10 flex flex-col overflow-hidden border border-teal-900/10">

        <header className="bg-teal-900 px-6 py-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-clay-600 flex items-center justify-center text-lg font-display font-bold text-white shrink-0">
            J
          </div>
          <div>
            <h1 className="text-white font-display font-semibold text-base leading-tight">
              Asisten Panduan Mobile JKN
            </h1>
            <p className="text-teal-100/70 text-xs mt-0.5">
              Dijawab berdasarkan panduan resmi BPJS Kesehatan
            </p>
          </div>
        </header>

        <FreshnessIndicator />

        <div className="flex-1 overflow-hidden">
          <ChatBox />
        </div>
      </div>
    </div>
  );
}

export default App;