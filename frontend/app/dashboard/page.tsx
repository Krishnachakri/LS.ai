"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface GPS {
  lat: number | null;
  lng: number | null;
  source: "browser" | "caller_described" | "unknown";
}

interface StructuredFacts {
  unconsciousness: boolean;
  breathing_difficulty: boolean;
  severe_bleeding: boolean;
  suspected_cardiac_emergency: boolean;
  head_injury: boolean;
  suspected_fracture: boolean;
}

interface Metrics {
  processingTimeMs: number;
  transcriptionTimeMs: number;
  parserTimeMs: number;
}

interface TimelineEvent {
  event: string;
  timestamp: string;
}

interface Incident {
  incidentId: string;
  timestamp: string;
  incidentMode: "voice" | "text";
  language: "en" | "te";
  incidentType: "Road Traffic Accident" | "Medical Emergency" | "Unknown";
  severity: "Critical" | "Urgent" | "Stable";
  severityScore: number;
  severityReason: string;
  victimCount: number;
  gps: GPS;
  callerTranscript: string;
  structuredFacts: StructuredFacts;
  metrics: Metrics;
  timeline: TimelineEvent[];
}

export default function DashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [connected, setConnected] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);
  const [highlightId, setHighlightId] = useState<string | null>(null);

  useEffect(() => {
    // Determine backend URLs dynamically from environment or default port 8000
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const wsUrl = backendUrl.replace(/^http/, "ws") + "/api/v1/incidents/live";
    
    let socket: WebSocket;
    let reconnectTimer: NodeJS.Timeout;

    const connectWebSocket = () => {
      console.log(`[*] Connecting dashboard socket to: ${wsUrl}`);
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setConnected(true);
        console.log("[+] WebSocket connection established.");
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          // 1. Heartbeat check handler
          if (message.event === "PING") {
            const pingTime = new Date(message.timestamp).getTime();
            const elapsed = Date.now() - pingTime;
            // Capture simulated/calculated network latency
            setLatency(elapsed > 0 ? elapsed : 1);
            socket.send("PONG");
            return;
          }

          // 2. Initial Cache Sync
          if (message.event === "INITIAL_SYNC") {
            const initialList: Incident[] = message.payload;
            setIncidents(initialList);
            if (initialList.length > 0) {
              setSelectedId(initialList[0].incidentId);
            }
          }
          
          // 3. New Live Ingestion Broadcaster
          else if (message.event === "NEW_INCIDENT") {
            const newIncident: Incident = message.payload;
            
            setIncidents((prev) => {
              // Deduplicate to prevent duplicates on manual sync fallbacks
              if (prev.some(item => item.incidentId === newIncident.incidentId)) {
                return prev;
              }
              return [newIncident, ...prev];
            });

            // Auto-select the incoming incident
            setSelectedId(newIncident.incidentId);
            
            // Trigger temporary fade/pulse highlight for the active card
            setHighlightId(newIncident.incidentId);
            setTimeout(() => {
              setHighlightId(null);
            }, 3000);
          }
        } catch (err) {
          console.error("Error parsing websocket message payload:", err);
        }
      };

      socket.onclose = () => {
        setConnected(false);
        setLatency(null);
        console.warn("[!] WebSocket connection closed. Reconnecting in 3 seconds...");
        reconnectTimer = setTimeout(connectWebSocket, 3000);
      };

      socket.onerror = (err) => {
        console.error("[!] WebSocket error occurred:", err);
        socket.close();
      };
    };

    connectWebSocket();

    return () => {
      if (socket) socket.close();
      clearTimeout(reconnectTimer);
    };
  }, []);

  // Filter incidents list based on Search Ingestion ID queries
  const filteredIncidents = incidents.filter(
    (inc) =>
      inc.incidentId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.incidentType.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.callerTranscript.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const selectedIncident = incidents.find((inc) => inc.incidentId === selectedId) || null;
  const criticalCount = incidents.filter(inc => inc.severity === "Critical").length;
  const urgentCount = incidents.filter(inc => inc.severity === "Urgent").length;
  const stableCount = incidents.filter(inc => inc.severity === "Stable").length;

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden antialiased">
      
      {/* 1. Header Control Bar */}
      <header className="flex items-center justify-between px-6 py-3 bg-zinc-900 border-b border-zinc-800 shrink-0">
        <div className="flex items-center gap-4">
          <span className="text-xl">🚨</span>
          <h1 className="text-base font-bold tracking-tight text-white uppercase flex items-center gap-2">
            LifeSaver.ai <span className="text-zinc-500 font-medium text-xs tracking-wider">Responder Operations Console</span>
          </h1>
          
          {/* Live Incident Statistics Ticker (RapidSOS Style) */}
          <div className="hidden lg:flex items-center gap-2 ml-6 text-xs font-mono select-none">
            <span className="text-zinc-650 font-semibold uppercase">Live Queue:</span>
            <div className={`px-2 py-0.5 border rounded-sm font-black ${criticalCount > 0 ? "bg-red-950/80 border-red-900/80 text-red-500 animate-pulse" : "bg-zinc-950 border-zinc-850 text-zinc-600"}`}>
              CRITICAL: {criticalCount}
            </div>
            <div className="px-2 py-0.5 bg-zinc-950 border border-zinc-850 rounded-sm font-black text-amber-500">
              URGENT: {urgentCount}
            </div>
            <div className="px-2 py-0.5 bg-zinc-950 border border-zinc-850 rounded-sm font-black text-emerald-500">
              STABLE: {stableCount}
            </div>
          </div>
        </div>
        
        {/* Real-time Heartbeat & Status Indicators */}
        <div className="flex items-center gap-5 text-xs select-none">
          <div className="flex items-center gap-2 font-mono font-semibold">
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`}></span>
            <span className={connected ? "text-emerald-400" : "text-red-500"}>
              {connected ? "LIVE" : "DISCONNECTED"}
            </span>
          </div>
          {latency !== null && (
            <div className="text-zinc-500 font-mono text-[11px]">
              NETWORK LATENCY: <span className="text-zinc-350 font-semibold">{latency} ms</span>
            </div>
          )}
          <Link
            href="/"
            className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 hover:text-white rounded border border-zinc-750 text-[11px] font-bold tracking-wide transition-all"
          >
            DISCONNECT CONSOLE
          </Link>
        </div>
      </header>

      {/* 2. Operations Panels Layout Grid */}
      <main className="flex-1 overflow-hidden p-4 bg-zinc-950">
        <div className="grid grid-cols-12 gap-4 h-full overflow-hidden">
          
          {/* PANEL A: Incidents Queue List (Left Column) */}
          <section className="col-span-12 md:col-span-3 border border-zinc-850 bg-zinc-900/40 rounded flex flex-col overflow-hidden">
            {/* Search Input block */}
            <div className="p-3 border-b border-zinc-850 bg-zinc-950/40 shrink-0">
              <input
                type="text"
                placeholder="FILTER INCIDENTS..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 focus:border-zinc-650 focus:outline-none rounded px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-700 font-mono tracking-wider transition-colors"
              />
            </div>
            
            {/* Active scrolling queue */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2 select-none">
              {filteredIncidents.length === 0 ? (
                <div className="text-center py-10 text-zinc-700 text-xs font-mono">
                  NO INCIDENTS IN QUEUE
                </div>
              ) : (
                filteredIncidents.map((incident) => {
                  const isSelected = incident.incidentId === selectedId;
                  const isHighlighted = incident.incidentId === highlightId;
                  
                  return (
                    <div
                      key={incident.incidentId}
                      onClick={() => setSelectedId(incident.incidentId)}
                      className={`p-3 rounded border cursor-pointer transition-all ${
                        isSelected 
                          ? "bg-zinc-900 border-zinc-650 shadow-sm" 
                          : "bg-zinc-950/40 border-zinc-850/60 hover:bg-zinc-900/50 hover:border-zinc-800"
                      } ${isHighlighted ? "border-red-500 animate-pulse" : ""} ${
                        incident.severity === "Critical" ? "border-l-4 border-l-red-650" :
                        incident.severity === "Urgent" ? "border-l-4 border-l-amber-500" :
                        "border-l-4 border-l-emerald-500"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-[9px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded-sm border font-mono ${
                          incident.severity === "Critical" ? "bg-red-950/40 border-red-900/40 text-red-500" :
                          incident.severity === "Urgent" ? "bg-amber-950/40 border-amber-900/40 text-amber-500" :
                          "bg-emerald-950/40 border-emerald-900/40 text-emerald-500"
                        }`}>
                          {incident.severity}
                        </span>
                        <span className="text-[9px] text-zinc-550 font-mono">
                          {new Date(incident.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
                        </span>
                      </div>
                      
                      <h3 className="font-bold text-xs text-white truncate font-mono">
                        {incident.incidentType.toUpperCase()}
                      </h3>
                      <p className="text-[11px] text-zinc-550 mt-1 line-clamp-2 italic">
                        "{incident.callerTranscript}"
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          </section>

          {/* PANEL B: Incident Details Panel (Center Column) */}
          <section className="col-span-12 md:col-span-6 border border-zinc-850 bg-zinc-900/40 rounded flex flex-col overflow-hidden">
            {selectedIncident ? (
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                
                {/* Detail Header block */}
                <div className="flex items-start justify-between border-b border-zinc-850 pb-3">
                  <div>
                    <h2 className="text-xl font-bold tracking-tight text-white font-mono">
                      {selectedIncident.incidentType.toUpperCase()}
                    </h2>
                    <span className="text-[10px] font-mono text-zinc-550 mt-1 block">
                      INCIDENT REF ID: {selectedIncident.incidentId}
                    </span>
                  </div>

                  <span className={`text-xs font-black uppercase tracking-widest px-2.5 py-1 rounded border font-mono ${
                    selectedIncident.severity === "Critical" ? "bg-red-950/80 border-red-900 text-red-500" :
                    selectedIncident.severity === "Urgent" ? "bg-amber-950/80 border-amber-900 text-amber-500" :
                    "bg-emerald-950/80 border-emerald-900 text-emerald-500"
                  }`}>
                    {selectedIncident.severity}
                  </span>
                </div>

                {/* Severity Assessment Console Bar */}
                <div className={`p-3 border select-none ${
                  selectedIncident.severity === "Critical" ? "bg-red-950/20 border-red-900/40 text-red-400" :
                  selectedIncident.severity === "Urgent" ? "bg-amber-950/20 border-amber-900/40 text-amber-400" :
                  "bg-emerald-950/20 border-emerald-900/40 text-emerald-400"
                }`}>
                  <h4 className="text-[10px] uppercase tracking-widest font-mono font-bold mb-1 text-zinc-550">Severity Assessment Logic</h4>
                  <p className="text-xs font-medium leading-relaxed font-mono">{selectedIncident.severityReason.toUpperCase()}</p>
                </div>

                {/* Caller Intake Mode Summary */}
                <div className="grid grid-cols-3 gap-3 font-mono select-none">
                  <div className="bg-zinc-950 border border-zinc-850 p-2.5 rounded-sm">
                    <span className="text-zinc-650 text-[9px] uppercase tracking-wider block font-bold">Input Method</span>
                    <span className="text-zinc-350 font-bold uppercase text-[11px] block mt-0.5">
                      {selectedIncident.incidentMode === "voice" ? "🎤 Multimodal Audio" : "⌨ Manual Text"}
                    </span>
                  </div>
                  <div className="bg-zinc-950 border border-zinc-850 p-2.5 rounded-sm">
                    <span className="text-zinc-650 text-[9px] uppercase tracking-wider block font-bold">Spoken Language</span>
                    <span className="text-zinc-350 font-bold uppercase text-[11px] block mt-0.5">
                      {selectedIncident.language === "te" ? "Telugu (తెలుగు)" : "English (EN)"}
                    </span>
                  </div>
                  <div className="bg-zinc-950 border border-zinc-850 p-2.5 rounded-sm">
                    <span className="text-zinc-650 text-[9px] uppercase tracking-wider block font-bold">Victim Count</span>
                    <span className="text-zinc-350 font-bold text-[11px] block mt-0.5">
                      {selectedIncident.victimCount} Individual(s)
                    </span>
                  </div>
                </div>

                {/* Raw Transcript View */}
                <div className="space-y-1.5">
                  <h4 className="text-zinc-550 text-[10px] uppercase tracking-widest font-mono font-bold">Caller Transcript</h4>
                  <div className="bg-zinc-950 border border-zinc-850 rounded p-4 text-xs italic leading-relaxed text-zinc-200 font-medium">
                    "{selectedIncident.callerTranscript}"
                  </div>
                </div>

                {/* Structured Facts Checklist */}
                <div className="space-y-2">
                  <h4 className="text-zinc-550 text-[10px] uppercase tracking-widest font-mono font-bold">Structured Incident Facts</h4>
                  <div className="grid grid-cols-2 gap-2.5 select-none font-mono">
                    {[
                      { key: "unconsciousness", label: "UNCONSCIOUSNESS" },
                      { key: "breathing_difficulty", label: "BREATHING DIFFICULTY" },
                      { key: "severe_bleeding", label: "SEVERE BLEEDING" },
                      { key: "suspected_cardiac_emergency", label: "CARDIAC EMERGENCY" },
                      { key: "head_injury", label: "CONSCIOUS HEAD INJURY" },
                      { key: "suspected_fracture", label: "SUSPECTED FRACTURE" }
                    ].map((item) => {
                      const val = selectedIncident.structuredFacts[item.key as keyof StructuredFacts];
                      return (
                        <div
                          key={item.key}
                          className={`flex items-center gap-2.5 p-2.5 border rounded-sm transition-colors ${
                            val 
                              ? "bg-red-950/10 border-red-900/30 text-red-400" 
                              : "bg-zinc-950/40 border-zinc-850/60 text-zinc-600"
                          }`}
                        >
                          <div className={`w-4 h-4 rounded-sm flex items-center justify-center text-[10px] font-black ${
                            val ? "bg-red-650 text-zinc-950 font-bold" : "border border-zinc-800"
                          }`}>
                            {val ? "✓" : ""}
                          </div>
                          <span className="font-bold text-[11px]">{item.label}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-zinc-700 text-xs font-mono">
                SELECT AN INCIDENT TO INITIALIZE DETAIL FEED
              </div>
            )}
          </section>

          {/* PANEL C: Timeline & Telemetry Metrics (Right Column) */}
          <section className="col-span-12 md:col-span-3 border border-zinc-850 bg-zinc-900/40 rounded flex flex-col overflow-hidden">
            {selectedIncident ? (
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                
                {/* 1. Telemetry Metrics Card */}
                <div className="space-y-2">
                  <h4 className="text-zinc-550 text-[10px] uppercase tracking-widest font-mono font-bold">Latency Telemetry</h4>
                  <div className="bg-zinc-950 border border-zinc-850 rounded p-3.5 space-y-2.5 text-xs font-mono">
                    <div className="flex justify-between">
                      <span className="text-zinc-650">ASR Transcribe:</span>
                      <span className="font-semibold text-zinc-350">
                        {selectedIncident.metrics.transcriptionTimeMs} ms
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-650">Context Parser:</span>
                      <span className="font-semibold text-zinc-350">
                        {selectedIncident.metrics.parserTimeMs} ms
                      </span>
                    </div>
                    <div className="flex justify-between border-t border-zinc-850 pt-2 font-bold text-zinc-250">
                      <span>Total Latency:</span>
                      <span className="text-emerald-400">
                        {selectedIncident.metrics.processingTimeMs} ms
                      </span>
                    </div>
                  </div>
                </div>

                {/* 2. Geolocation Coordinates Card */}
                <div className="space-y-2">
                  <h4 className="text-zinc-550 text-[10px] uppercase tracking-widest font-mono font-bold">Intake Location</h4>
                  <div className="bg-zinc-950 border border-zinc-850 rounded p-3.5 space-y-2.5 text-xs font-mono">
                    <div className="flex justify-between items-center">
                      <span className="text-zinc-650">GPS Source:</span>
                      <span className={`text-[9px] uppercase font-black px-1.5 py-0.5 rounded-sm border ${
                        selectedIncident.gps.source === "browser" 
                          ? "bg-emerald-950/40 border-emerald-900/40 text-emerald-400" 
                          : "bg-amber-950/40 border-amber-900/40 text-amber-500"
                      }`}>
                        {selectedIncident.gps.source === "browser" ? "Browser GPS" : "Manual Landmark"}
                      </span>
                    </div>
                    
                    {selectedIncident.gps.lat !== null && selectedIncident.gps.lng !== null ? (
                      <>
                        <div className="flex justify-between">
                           <span className="text-zinc-650">Latitude:</span>
                           <span className="font-semibold text-zinc-350">{selectedIncident.gps.lat.toFixed(5)}</span>
                        </div>
                        <div className="flex justify-between">
                           <span className="text-zinc-650">Longitude:</span>
                           <span className="font-semibold text-zinc-350">{selectedIncident.gps.lng.toFixed(5)}</span>
                        </div>
                        
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${selectedIncident.gps.lat},${selectedIncident.gps.lng}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-center w-full py-1.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white rounded text-[10px] font-bold text-zinc-400 transition-colors select-none"
                        >
                          OPEN MAP RADIAL
                        </a>
                      </>
                    ) : (
                      <div className="text-zinc-700 italic text-[11px] text-center py-1">
                        NO COORDINATES OBTAINED
                      </div>
                    )}
                  </div>
                </div>

                {/* 3. Event Life-cycle Timeline */}
                <div className="space-y-3 select-none">
                  <h4 className="text-zinc-550 text-[10px] uppercase tracking-widest font-mono font-bold">Operations Timeline</h4>
                  <div className="relative border-l border-zinc-850 ml-2 space-y-4">
                    {selectedIncident.timeline.map((event, idx) => (
                      <div key={idx} className="relative pl-5 font-mono">
                        {/* Dot indicator */}
                        <div className="absolute -left-1 top-1.5 w-2.5 h-2.5 rounded-full bg-zinc-800 border border-zinc-950"></div>
                        <div className="flex justify-between items-baseline gap-2">
                          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-wide">
                            {event.event.replace("_", " ")}
                          </span>
                          <span className="text-[9px] text-zinc-550">
                            {new Date(event.timestamp).toLocaleTimeString([], { hour12: false, fractionalSecondDigits: 3 } as any)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-zinc-700 text-xs font-mono">
                NO CORRESPONDING DATA
              </div>
            )}
          </section>

        </div>
      </main>

    </div>
  );
}
