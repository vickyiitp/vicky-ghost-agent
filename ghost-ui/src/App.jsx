import React, { useState, useEffect } from 'react';
import { Shield, Zap, AlertTriangle, Download, Fingerprint, Activity, Play } from 'lucide-react';

export default function App() {
  const [url, setUrl] = useState("https://x.com/search?q=freelance");
  const [instruction, setInstruction] = useState("Find freelance web developer jobs from Feb 8-9");
  const [logs, setLogs] = useState([]);
  const [isScraping, setIsScraping] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [activeIdentity, setActiveIdentity] = useState("GHOST-7X");
  const [reportUrl, setReportUrl] = useState(null);
  const [warmerStatus, setWarmerStatus] = useState("OFFLINE");

  // Poll warmer status
  useEffect(() => {
    const checkStatus = async () => {
        try {
            const res = await fetch('http://localhost:8000/warmer-status');
            const data = await res.json();
            setWarmerStatus(data.status);
        } catch (e) {
            setWarmerStatus("OFFLINE");
        }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000); // Check every 10s
    return () => clearInterval(interval);
  }, []);

  // Cooldown Timer
  useEffect(() => {
    let interval;
    if (cooldown > 0) {
      interval = setInterval(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    } else {
      setIsLocked(false);
    }
    return () => clearInterval(interval);
  }, [cooldown]);

  const addLog = (msg) => {
    setLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 99)]);
  };

  const startGhostMode = async () => {
    if (cooldown > 0 || isScraping) return;

    setIsScraping(true);
    setIsLocked(true);
    setCooldown(60); // 1 minute hardware cooldown to protect API quotas
    addLog("[INIT] Ghost Sequence Initiated...");
    addLog(`[TARGET] ${url}`);

    try {
      const response = await fetch('http://localhost:8000/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          command: instruction
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      
      if (data.error) {
        addLog(`[ERROR] Mission Failed: ${data.error}`);
      } else {
        addLog(`[SUCCESS] Mission Complete.`);
        if (typeof data.data === 'string') {
             addLog(`[DATA] ${data.data.substring(0, 100)}...`);
        } else {
             addLog(`[DATA] ${JSON.stringify(data.data).substring(0, 100)}...`);
        }
        addLog(`[REPORT] Generated: ${data.report}`);
        if(data.report_url) setReportUrl(data.report_url);
      }

    } catch (error) {
      addLog(`[FATAL] Network Connection Failed: ${error.message}`);
      console.error(error);
    } finally {
      setIsScraping(false);
    }
  };

  const triggerWipe = () => {
    addLog("[WARN] SELF-DESTRUCT SEQUENCE INITIATED");
    addLog("[WARN] FLUSHING LOCAL CACHE...");
    setTimeout(() => {
        setLogs([]);
        setUrl("");
        setInstruction("");
        alert("SYSTEM PURGED.");
    }, 1000);
  };

  return (
    <div className="bg-black min-h-screen text-green-500 font-mono p-8 selection:bg-green-900 border-t-4 border-green-600">
      <div className="max-w-6xl mx-auto">
      
      {/* Header with Dashboard */}
      <div className="flex justify-between items-end mb-8 border-b border-green-800 pb-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tighter flex items-center gap-2 text-white">
            <Fingerprint className="w-8 h-8 animate-pulse text-green-500" />
            VICKY-GHOST<span className="text-green-600">_AGENT</span>
          </h1>
          <p className="opacity-70 text-sm mt-1 text-green-500">v:2.1.0 // STATUS: {isScraping ? <span className="text-yellow-400 animate-pulse">HUNTING</span> : "IDLE"}</p>
        </div>
        
        {/* Identity Matrix Dashboard */}
        <div className="text-right">
             <div className="text-xs uppercase opacity-50 mb-1 text-green-400">Active Identity Node</div>
             <div className="flex items-center gap-2 bg-green-900/20 px-4 py-2 rounded border border-green-800">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-ping"></div>
                <span className="font-bold text-green-400">{activeIdentity}</span>
             </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Status Panel */}
          <div className="bg-zinc-950 p-4 border border-green-900/50 rounded flex items-center gap-4">
             <Shield className="w-8 h-8 text-green-700" />
             <div>
                <div className="text-xs uppercase opacity-50">Security Protocol</div>
                <div className="font-bold text-white">ENCRYPTED</div>
             </div>
          </div>

          <div className="bg-zinc-950 p-4 border border-green-900/50 rounded flex items-center gap-4">
             <div className={`w-3 h-3 rounded-full animate-pulse ${warmerStatus === 'ACTIVE' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : warmerStatus === 'IDLE' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
             <div>
                <div className="text-xs uppercase opacity-50">Shadow Warmer</div>
                <div className={`font-bold ${warmerStatus === 'ACTIVE' ? 'text-green-500' : warmerStatus === 'IDLE' ? 'text-yellow-500' : 'text-red-500'}`}>
                    {warmerStatus}
                </div>
             </div>
          </div>
            
          <button 
              onClick={triggerWipe} 
              className="border-2 border-red-600 bg-red-900/10 text-red-600 hover:bg-red-600 hover:text-white px-6 py-3 transition-all font-bold animate-pulse flex items-center justify-center gap-2 rounded text-sm tracking-widest"
          >
              <AlertTriangle className="w-4 h-4" /> SELF-DESTRUCT
          </button>
      </div>
          
          {/* Controls */}
          <div className="mb-8 grid grid-cols-12 gap-4">
              <div className="col-span-12 md:col-span-8 p-6 bg-zinc-950 border border-green-900/30 rounded-lg">
                    <p className="text-green-500 font-mono text-xs mb-2 opacity-70 uppercase tracking-widest">{">"} AI_DIRECTIVE_INPUT</p>
                    <div className="relative">
                        <input 
                            type="text" 
                            placeholder="TARGET URL (e.g., https://x.com/search?q=freelance)"
                            className="w-full bg-black border border-green-900/50 p-4 mb-4 text-green-400 font-mono focus:ring-1 focus:ring-green-500 outline-none placeholder:text-green-900"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                        />
                        <textarea 
                            className="w-full bg-black border border-green-900/50 p-4 text-green-400 font-mono focus:ring-1 focus:ring-green-500 outline-none placeholder:text-green-900 min-h-[100px]"
                            placeholder="COMMAND (e.g. Find freelance web developer opportunities and extracting user, content, source link)"
                            value={instruction}
                            onChange={(e) => setInstruction(e.target.value)}
                        />
                    </div>
                    <button 
                        onClick={startGhostMode} 
                        disabled={isScraping || isLocked}
                        className={`mt-4 w-full font-bold py-3 uppercase tracking-tighter transition-all flex justify-center items-center gap-2 group ${
                            isLocked 
                            ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-700'
                            : 'bg-green-900 hover:bg-green-700 text-black'
                        }`}
                    >
                       {isScraping ? <Activity className="animate-spin w-4 h-4"/> : isLocked ? <Shield className="w-4 h-4 animate-pulse"/> : <Play className="w-4 h-4 fill-black"/>}
                       {isScraping ? "Processing..." : isLocked ? `SYSTEM COOLING DOWN (${cooldown}s)` : "Initiate Ghost Sequence"}
                    </button>
                    {isLocked && <p className="text-center text-[10px] text-green-500/50 mt-2 font-mono">PREVENTING API QUOTA EXHAUSTION</p>}
              </div>

              <div className="col-span-12 md:col-span-4 p-4 bg-zinc-950 border border-green-900/30 rounded-lg overflow-y-auto max-h-[300px] font-mono text-xs scrollbar-hide">
                  <div className="flex items-center gap-2 mb-2 text-green-700 border-b border-green-900/30 pb-2">
                    <Activity className="w-3 h-3"/> SYSTEM LOGS
                  </div>
                  <div className="space-y-1">
                     {logs.length === 0 && <span className="opacity-30">Waiting for events...</span>}
                     {logs.map((log, i) => (
                        <p key={i} className="text-green-500/80 break-words">{log}</p>
                     ))}
                  </div>
              </div>
          </div>

          {/* Visualization / Terminal */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[400px]">
                {/* TERMINAL LOGS */}
                <div className="bg-black border border-green-800 rounded shadow-2xl overflow-hidden flex flex-col relative group">
                    <div className="bg-green-900/20 p-2 border-b border-green-800 flex justify-between items-center px-4">
                        <span className="text-xs font-bold text-green-600">TERMINAL OUTPUT</span>
                        <div className="flex gap-2">
                            <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                            <div className="w-2 h-2 rounded-full bg-yellow-500/50"></div>
                            <div className="w-2 h-2 rounded-full bg-green-500/50"></div>
                        </div>
                    </div>
                    <div className="p-4 font-mono text-xs text-green-300 opacity-80 overflow-y-auto flex-1">
                        <p className="mb-2">{">"} SYSTEM_READY</p>
                        <p className="mb-2">{">"} CONNECTED_TO_GHOST_NET</p>
                        {isScraping && (
                            <>
                                <p className="mb-2 animate-pulse">{">"} PLAYWRIGHT_ENGINE_STARTING...</p>
                                <p className="mb-2">{">"} BYPASSING_PUPPETEER_DETECTION...</p>
                                <p className="mb-2">{">"} ANALYZING_DOM_STRUCTURE...</p>
                            </>
                        )}
                        {!isScraping && logs.length > 0 && <p className="mb-2">{">"} IDLE...</p>}
                    </div>
                </div>

                 {/* PLACEHOLDER FOR PDF PREVIEW OR DATA */}
                <div className="bg-black border border-green-800 rounded shadow-2xl flex items-center justify-center relative overflow-hidden">
                     <div className="absolute inset-0 bg-green-900/5 grid-pattern pointer-events-none"></div>
                     <div className="text-center z-10 w-full px-4">
                        {reportUrl ? (
                            <div className="animate-in fade-in zoom-in duration-500">
                                <a 
                                    href={reportUrl} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    className="block w-full bg-green-900/20 border border-green-500/50 hover:bg-green-500 hover:text-black text-green-400 p-8 rounded transition-all group cursor-pointer"
                                >
                                    <Download className="w-16 h-16 mx-auto mb-4 group-hover:scale-110 transition-transform" />
                                    <h3 className="text-xl font-bold mb-2">INTELLIGENCE REPORT ACQUIRED</h3>
                                    <p className="text-xs opacity-70 font-mono">CLICK TO DOWNLOAD SECURE PDF</p>
                                </a>
                            </div>
                        ) : (
                            <>
                                <Download className="w-12 h-12 text-green-800 mx-auto mb-4 opacity-50" />
                                <p className="text-green-800 text-xs">AWAITING GENERATION...</p>
                            </>
                        )}
                     </div>
                </div>
          </div>
      </div>
    </div>
  );
}
