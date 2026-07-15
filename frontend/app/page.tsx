import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-zinc-100 font-sans p-6">
      <main className="w-full max-w-2xl text-center space-y-8">
        {/* Branding & Vision */}
        <div className="space-y-4">
          <h1 className="text-5xl font-extrabold tracking-tight text-white">
            LifeSaver.ai <span className="text-zinc-500 font-medium text-3xl">(LS.ai)</span>
          </h1>
          <p className="text-lg text-zinc-400 max-w-lg mx-auto">
            A real-time AI-powered emergency coordination platform. Transforming panicked emergency descriptions into structured, actionable incident feeds instantly.
          </p>
        </div>

        {/* Portal Entry Links */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md mx-auto pt-6">
          <Link
            href="/caller"
            className="flex flex-col items-center justify-center p-6 rounded-xl border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900 hover:border-zinc-700 transition-all group"
          >
            <span className="text-2xl mb-2 group-hover:scale-110 transition-transform">🚨</span>
            <span className="font-semibold text-lg text-white">Caller Portal</span>
            <span className="text-xs text-zinc-500 mt-1">Report an emergency</span>
          </Link>

          <Link
            href="/dashboard"
            className="flex flex-col items-center justify-center p-6 rounded-xl border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900 hover:border-zinc-700 transition-all group"
          >
            <span className="text-2xl mb-2 group-hover:scale-110 transition-transform">💻</span>
            <span className="font-semibold text-lg text-white">Responder Dashboard</span>
            <span className="text-xs text-zinc-500 mt-1">Live timeline and severity feed</span>
          </Link>
        </div>

        {/* Design Principles / Pitch Footer */}
        <div className="pt-12 text-xs text-zinc-600 border-t border-zinc-900 max-w-xs mx-auto">
          LifeSaver.ai (LS.ai) • Live Coordinator Layer V1
        </div>
      </main>
    </div>
  );
}
