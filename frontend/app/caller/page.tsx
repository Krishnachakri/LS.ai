"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

// 2-Language UI Dictionary for Zero Configuration Automatic Adaptation
const translations = {
  en: {
    title: "LifeSaver.ai",
    subtitle: "Emergency Intake Portal",
    emergencyBtn: "🚨 PRESS TO RECORD EMERGENCY",
    tapToSpeak: "TAP TO START EMERGENCY REPORT",
    recording: "RECORDING... TAP TO PREVIEW",
    textFallback: "Or Type Emergency Details",
    typePlaceholder: "Describe the emergency in your language (e.g., car crash on main road, chest pain)...",
    manualLocation: "Location Description / Landmarks",
    locPlaceholder: "Street name, landmark, address if GPS is inaccurate...",
    submit: "✔ Send Emergency Report",
    submitting: "Analyzing Emergency Context...",
    successTitle: "✔ Emergency Report Sent",
    successSubtitle: "Emergency response is being coordinated.",
    transcriptLabel: "Voice Transcript Preview:",
    backToHub: "← Return to Hub",
    micError: "Microphone blocked. Switched to text fallback mode.",
    gpsError: "GPS unavailable. Please enter landmarks manually.",
    stage1: "Report Received",
    stage2: "Speech Analyzed",
    stage3: "Severity Classified",
    stage4: "Forwarded to Responders",
    sendConfirm: "Verify description below before sending:"
  },
  te: {
    title: "LifeSaver.ai",
    subtitle: "అవసర సహాయ కేంద్రం",
    emergencyBtn: "🚨 అత్యవసర నివేదికను రికార్డ్ చేయండి",
    tapToSpeak: "అత్యవసర నివేదికను ప్రారంభించడానికి నొక్కండి",
    recording: "వింటున్నాము... ప్రివ్యూ కోసం నొక్కండి",
    textFallback: "లేదా వివరాలను ఇక్కడ టైప్ చేయండి",
    typePlaceholder: "ఏమి జరిగిందో మీ భాషలో వివరించండి (ఉదా. రోడ్డు ప్రమాదం, గుండెనొప్పి)...",
    manualLocation: "స్థాన వివరాలు / ల్యాండ్‌మార్క్‌లు",
    locPlaceholder: "వీధి పేరు, మైలురాయి, లేదా చిరునామా...",
    submit: "అత్యవసర సమాచారాన్ని పంపండి",
    submitting: "వివరాలను విశ్లేషిస్తున్నాము...",
    successTitle: "✔ అత్యవసర నివేదిక పంపబడింది",
    successSubtitle: "సహాయం అందించడానికి చర్యలు చేపట్టబడ్డాయి.",
    transcriptLabel: "రికార్డింగ్ వివరణ ప్రివ్యూ:",
    backToHub: "← తిరిగి వెళ్ళండి",
    micError: "మైక్రోఫోన్ నిలిపివేయబడింది. టెక్స్ట్ మోడ్‌కు మార్చబడింది.",
    gpsError: "జీపీఎస్ అందుబాటులో లేదు. దయచేసి స్థాన వివరాలు నమోదు చేయండి.",
    stage1: "నివేదిక అందింది",
    stage2: "సంభాషణ విశ్లేషించబడింది",
    stage3: "తీవ్రత నిర్ధారించబడింది",
    stage4: "సిబ్బందికి పంపబడింది",
    sendConfirm: "సమర్పించడానికి ముందు వివరాలను తనిఖీ చేయండి:"
  }
};

const getStageIndex = (stage: string) => {
  const stages = ["idle", "received", "transcribing", "extracting", "computing", "broadcasting", "sent"];
  return stages.indexOf(stage);
};

export default function CallerPage() {
  const [lang, setLang] = useState<"en" | "te">("en");
  const [status, setStatus] = useState<"idle" | "recording" | "transcribing" | "preview" | "processing" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");
  
  // Geolocation states
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [gpsSource, setGpsSource] = useState<"browser" | "caller_described" | "unknown">("unknown");
  
  // Ingest states
  const [textFallback, setTextFallback] = useState("");
  const [manualLocation, setManualLocation] = useState("");
  const [showTextFallback, setShowTextFallback] = useState(false);
  
  // Audio recording states
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  
  // Timing telemetry refs
  const recordingStartTimeRef = useRef<number>(0);
  const recordingStopCallTimeRef = useRef<number>(0);
  const [renderStartTime, setRenderStartTime] = useState<number | null>(null);
  
  // Progress tracker state
  const [progressStage, setProgressStage] = useState<"idle" | "received" | "transcribing" | "extracting" | "computing" | "broadcasting" | "sent">("idle");
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const startProgressAnimation = () => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }
    
    setProgressStage("received");
    const stages: Array<"received" | "transcribing" | "extracting" | "computing" | "broadcasting"> = [
      "received",
      "transcribing",
      "extracting",
      "computing",
      "broadcasting"
    ];
    
    let currentStageIndex = 0;
    progressIntervalRef.current = setInterval(() => {
      if (currentStageIndex < stages.length - 1) {
        currentStageIndex++;
        setProgressStage(stages[currentStageIndex]);
      } else {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      }
    }, 3000); // 3 seconds per stage
  };

  const stopProgressAnimation = (finalStage?: "idle" | "sent") => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    if (finalStage) {
      setProgressStage(finalStage);
    }
  };

  // Ingestion Response Results
  const [result, setResult] = useState<{
    transcript: string;
    severity: string;
    severityScore: number;
    metrics: { processingTimeMs: number; transcriptionTimeMs: number; parserTimeMs: number };
  } | null>(null);

  const t = translations[lang];

  // Detect browser locale on mount to initialize language
  useEffect(() => {
    if (typeof window !== "undefined" && navigator.language) {
      const browserLang = navigator.language.split("-")[0];
      if (browserLang === "te") {
        setLang("te");
      }
    }
    
    // Auto-request browser GPS geolocation
    requestGeolocation();
  }, []);

  // Track React render and layout commit telemetry
  useEffect(() => {
    if ((status === "preview" || status === "success") && renderStartTime !== null) {
      const renderDuration = performance.now() - renderStartTime;
      console.log(`[Telemetry] Frontend Render (Transition to ${status}): ${Math.round(renderDuration)} ms`);
    }
  }, [status, renderStartTime]);

  const requestGeolocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLat(position.coords.latitude);
          setLng(position.coords.longitude);
          setGpsSource("browser");
        },
        (error) => {
          console.warn("GPS Permission Denied:", error);
          setGpsSource("caller_described");
          setErrorMsg(t.gpsError);
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    } else {
      setGpsSource("caller_described");
    }
  };

  // Audio Recording Controls
  const startRecording = async () => {
    audioChunksRef.current = [];
    setRecordingSeconds(0);
    setErrorMsg("");
    setAudioBlob(null);
    setResult(null);
    
    try {
      // Request 16kHz mono audio to optimize payload size (~65% reduction)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const onStopCallTime = performance.now();
        const generatedBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setAudioBlob(generatedBlob);
        
        // Stop all track media streams
        stream.getTracks().forEach(track => track.stop());
        
        const recDuration = recordingStopCallTimeRef.current - recordingStartTimeRef.current;
        const encDuration = onStopCallTime - recordingStopCallTimeRef.current;
        console.log(`[Telemetry] Audio Recording Duration: ${Math.round(recDuration)} ms`);
        console.log(`[Telemetry] Audio Encoding (Blob Assembly): ${Math.round(encDuration)} ms`);
        
        // Transcribe audio first so caller can preview
        await transcribeOnly(generatedBlob);
      };

      mediaRecorderRef.current = recorder;
      recordingStartTimeRef.current = performance.now();
      recorder.start();
      setIsRecording(true);
      setStatus("recording");

      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);

    } catch (err) {
      setErrorMsg(`${t.micError} Detail: ${err}`);
      setShowTextFallback(true);
      setStatus("idle");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      recordingStopCallTimeRef.current = performance.now();
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  const handleRecordToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Transcribes the audio locally without finalizing/broadcasting yet
  const transcribeOnly = async (blob: Blob) => {
    setStatus("transcribing");
    startProgressAnimation();
    const incidentId = crypto.randomUUID();
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");
    formData.append("incidentMode", "voice");
    formData.append("language_code", lang);
    formData.append("incident_id", incidentId);
    if (lat !== null) formData.append("latitude", lat.toString());
    if (lng !== null) formData.append("longitude", lng.toString());
 
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
 
    try {
      const uploadStart = performance.now();
      const res = await fetch(`${backendUrl}/api/v1/incidents/report`, {
        method: "POST",
        body: formData,
      });
 
      if (!res.ok) {
        const errorJson = await res.json().catch(() => ({}));
        const backendError = errorJson.detail || `Status ${res.status}`;
        throw new Error(backendError);
      }
      
      const data = await res.json();
      const uploadEnd = performance.now();
      
      const roundtrip = uploadEnd - uploadStart;
      const backendProcessing = data.metrics?.processingTimeMs || 0;
      const networkTransit = roundtrip - backendProcessing;
      console.log(`[Telemetry] HTTP Ingestion Response (Roundtrip): ${Math.round(roundtrip)} ms`);
      console.log(`[Telemetry] HTTP Upload & Network Transit: ${Math.round(networkTransit)} ms`);
      
      if (data.language === "te") setLang("te");
 
      setRenderStartTime(performance.now());
      setResult({
        transcript: data.callerTranscript,
        severity: data.severity,
        severityScore: data.severityScore,
        metrics: data.metrics
      });
      setStatus("preview");
    } catch (err: any) {
      setErrorMsg(`Voice transcription failed: ${err.message || err}. Fallback to text mode.`);
      setShowTextFallback(true);
      setStatus("idle");
    } finally {
      stopProgressAnimation("sent");
    }
  };
 
  // Finalizes the emergency report sending trigger
  const handleFinalSend = () => {
    setStatus("processing");
    setTimeout(() => {
      setRenderStartTime(performance.now());
      setStatus("success");
    }, 1200); // 1.2s visual staging
  };
 
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textFallback.trim()) return;
 
    setStatus("processing");
    startProgressAnimation();
    const incidentId = crypto.randomUUID();
    const formData = new FormData();
    formData.append("text_fallback", textFallback);
    formData.append("incidentMode", "text");
    formData.append("incident_id", incidentId);
    if (lat !== null) formData.append("latitude", lat.toString());
    if (lng !== null) formData.append("longitude", lng.toString());
    if (manualLocation.trim()) {
      formData.append("text_fallback", `${textFallback} (Landmarks: ${manualLocation})`);
    }
    formData.append("language_code", lang);
 
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
 
    try {
      const uploadStart = performance.now();
      const res = await fetch(`${backendUrl}/api/v1/incidents/report`, {
        method: "POST",
        body: formData,
      });
 
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      const uploadEnd = performance.now();
      
      const roundtrip = uploadEnd - uploadStart;
      const backendProcessing = data.metrics?.processingTimeMs || 0;
      const networkTransit = roundtrip - backendProcessing;
      console.log(`[Telemetry] HTTP Ingestion Response (Roundtrip): ${Math.round(roundtrip)} ms`);
      console.log(`[Telemetry] HTTP Upload & Network Transit: ${Math.round(networkTransit)} ms`);
      
      if (data.language === "te") setLang("te");
 
      setRenderStartTime(performance.now());
      setResult({
        transcript: data.callerTranscript,
        severity: data.severity,
        severityScore: data.severityScore,
        metrics: data.metrics
      });
      setStatus("success");
    } catch (err: any) {
      setErrorMsg(`Submission failed: ${err.message}`);
      setStatus("error");
    } finally {
      stopProgressAnimation("sent");
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-zinc-100 font-sans p-4">
      <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-8">
        
        {/* Header */}
        <div className="text-center border-b border-zinc-800/60 pb-5">
          <h1 className="text-4xl font-black tracking-tight text-white">{t.title}</h1>
          <p className="text-sm text-zinc-500 mt-2 uppercase tracking-widest font-semibold">{t.subtitle}</p>
        </div>

        {errorMsg && (
          <div className="p-4 bg-red-950/40 border border-red-900/60 rounded-xl text-sm text-red-400 text-center font-medium">
            {errorMsg}
          </div>
        )}

        {/* Ingestion Panel States */}
        {status === "success" && result ? (
          /* 1. SUCCESS CHRONOLOGICAL PROGRESSION BAR */
          <div className="space-y-8 animate-fade-in py-4">
            <div className="text-center space-y-2">
              <h2 className="text-3xl font-black text-emerald-500 tracking-tight">{t.successTitle}</h2>
              <p className="text-base text-zinc-400">{t.successSubtitle}</p>
            </div>

            {/* Cronological Status Steps */}
            <div className="space-y-4 max-w-sm mx-auto pt-4">
              {[
                { label: t.stage1, active: true },
                { label: t.stage2, active: true },
                { label: t.stage3, active: true },
                { label: t.stage4, active: true }
              ].map((step, idx) => (
                <div key={idx} className="flex items-center gap-4 text-base font-semibold">
                  <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center text-xs text-zinc-900 font-black">
                    ✓
                  </div>
                  <span className="text-zinc-200">{step.label}</span>
                </div>
              ))}
            </div>

            <button
              onClick={() => {
                setStatus("idle");
                setResult(null);
                setAudioBlob(null);
                setTextFallback("");
                setManualLocation("");
              }}
              className="w-full py-4 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-650 text-white font-bold rounded-2xl transition-colors text-base"
            >
              Report Another Emergency
            </button>
          </div>
        ) : status === "processing" || status === "transcribing" ? (
          /* 2. DYNAMIC MULTI-STAGE PROGRESS TRACKER */
          <div className="space-y-6 py-6 animate-fade-in text-center">
            <div className="space-y-2">
              <div className="inline-block w-10 h-10 border-4 border-zinc-800 border-t-red-500 rounded-full animate-spin mb-2"></div>
              <h2 className="text-xl font-bold text-white tracking-tight">🚨 Emergency Report Processing</h2>
            </div>
            
            <div className="space-y-4 max-w-sm mx-auto border border-zinc-800 bg-zinc-950/40 p-6 rounded-2xl text-left">
              {[
                { key: "received", label: "Audio Received", minStage: "received" },
                { key: "transcribing", label: "Transcribing Voice...", minStage: "transcribing" },
                { key: "extracting", label: "Extracting Emergency Facts", minStage: "extracting" },
                { key: "computing", label: "Computing Severity", minStage: "computing" },
                { key: "broadcasting", label: "Alerting Responders", minStage: "broadcasting" },
              ].map((step, idx) => {
                const stepIdx = getStageIndex(step.minStage);
                const currentIdx = getStageIndex(progressStage);
                
                const isCompleted = currentIdx > stepIdx;
                const isActive = progressStage === step.minStage;
                
                return (
                  <div key={idx} className="flex items-center gap-3 text-sm font-semibold select-none">
                    {isCompleted ? (
                      <span className="text-emerald-500 font-black">✓</span>
                    ) : isActive ? (
                      <span className="text-red-500 animate-pulse font-black">⏳</span>
                    ) : (
                      <span className="text-zinc-700 font-black">⬜</span>
                    )}
                    <span className={isCompleted ? "text-zinc-400 font-normal line-through decoration-zinc-700/60" : isActive ? "text-red-400 font-bold" : "text-zinc-650"}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-zinc-500 italic font-medium">Estimated processing time: 20–30 seconds</p>
          </div>
        ) : status === "preview" && result ? (
          /* 3. VERIFICATION TRANSCRIPT PREVIEW */
          <div className="space-y-6 animate-fade-in">
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-white">{t.sendConfirm}</h2>
            </div>
            
            <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-5 text-left text-base">
              <span className="text-zinc-500 font-bold block text-xs uppercase tracking-wider mb-2">{t.transcriptLabel}</span>
              <p className="text-zinc-100 font-medium italic text-lg leading-relaxed">"{result.transcript}"</p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={handleFinalSend}
                className="flex-1 py-4 bg-emerald-600 hover:bg-emerald-700 text-zinc-950 font-black rounded-2xl transition-colors text-base text-center"
              >
                Send Report
              </button>
              <button
                onClick={() => {
                  setStatus("idle");
                  setResult(null);
                  startRecording();
                }}
                className="py-4 px-6 bg-zinc-800 hover:bg-zinc-700 text-white font-bold rounded-2xl transition-colors text-base text-center"
              >
                🎤 Record Again
              </button>
            </div>
          </div>
        ) : (
          /* 4. ACTIVE EMERGENCY INTAKE */
          <div className="space-y-8">
            
            {!showTextFallback && (
              <div className="flex flex-col items-center justify-center space-y-6">
                
                {/* BIG Emergency Button with Pulse effect */}
                <button
                  onClick={handleRecordToggle}
                  className={`w-48 h-48 rounded-full flex flex-col items-center justify-center transition-all ${
                    isRecording 
                    ? "bg-red-600 scale-105 border-8 border-red-950/80 shadow-[0_0_30px_rgba(220,38,38,0.3)]" 
                    : "bg-red-800 hover:bg-red-700 border-8 border-zinc-950 shadow-lg"
                  }`}
                >
                  <span className="text-5xl animate-bounce">🚨</span>
                  <span className="text-xs font-black text-white uppercase tracking-widest mt-3">
                    {isRecording ? "STOP" : "SPEAK"}
                  </span>
                </button>

                <div className="text-center space-y-1">
                  <h3 className={`text-xl font-bold tracking-tight ${isRecording ? "text-red-500" : "text-zinc-200"}`}>
                    {isRecording ? `${t.recording} (${recordingSeconds}s)` : t.emergencyBtn}
                  </h3>
                  <p className="text-sm text-zinc-500 font-semibold">{t.tapToSpeak}</p>
                </div>
              </div>
            )}

            {/* Apple Voice Memo subtle pulsing bars */}
            {isRecording && (
              <div className="flex items-center justify-center gap-1.5 py-4">
                {[12, 24, 40, 24, 12, 18, 30, 18, 12].map((h, i) => (
                  <div 
                    key={i} 
                    className="w-1 bg-red-600 rounded-full animate-pulse" 
                    style={{ 
                      height: `${h}px`,
                      animationDelay: `${i * 100}ms`
                    }}
                  />
                ))}
              </div>
            )}

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => setShowTextFallback(prev => !prev)}
                className="text-sm text-zinc-500 hover:text-zinc-300 font-bold underline underline-offset-4 transition-colors"
              >
                {showTextFallback ? "← Use Voice Recording" : t.textFallback}
              </button>
            </div>

            {/* Text Fallback Form */}
            {showTextFallback && (
              <form onSubmit={handleTextSubmit} className="space-y-5 text-sm animate-fade-in">
                <div className="space-y-2">
                  <label className="text-zinc-400 font-black block text-xs uppercase tracking-wider">
                    Emergency Description
                  </label>
                  <textarea
                    required
                    value={textFallback}
                    onChange={(e) => setTextFallback(e.target.value)}
                    placeholder={t.typePlaceholder}
                    rows={4}
                    className="w-full bg-zinc-950 border border-zinc-800 focus:border-zinc-700 focus:outline-none rounded-2xl p-4 text-lg text-zinc-100 placeholder-zinc-700 transition-colors"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-zinc-400 font-black block text-xs uppercase tracking-wider">
                    {t.manualLocation}
                  </label>
                  <input
                    type="text"
                    value={manualLocation}
                    onChange={(e) => setManualLocation(e.target.value)}
                    placeholder={t.locPlaceholder}
                    className="w-full bg-zinc-950 border border-zinc-800 focus:border-zinc-700 focus:outline-none rounded-2xl px-4 py-3 text-base text-zinc-100 placeholder-zinc-700 transition-colors"
                  />
                </div>

                <button
                  type="submit"
                  disabled={!textFallback.trim()}
                  className="w-full py-4 bg-red-600 hover:bg-red-700 disabled:bg-zinc-800 disabled:text-zinc-650 font-black rounded-2xl transition-all text-base uppercase tracking-widest text-white"
                >
                  {t.submit}
                </button>
              </form>
            )}
          </div>
        )}

        {/* Back Link */}
        <div className="text-center pt-3 border-t border-zinc-800/40">
          <Link
            href="/"
            onClick={() => {
              if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
            }}
            className="text-sm text-zinc-500 hover:text-zinc-300 font-bold transition-colors inline-block"
          >
            {t.backToHub}
          </Link>
        </div>
      </div>
    </div>
  );
}
