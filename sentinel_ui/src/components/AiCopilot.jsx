import React, { useState } from 'react';
import { Bot, Send, Sparkles, X, ShieldAlert, Car, MapPin, Zap, CheckCircle2, Terminal } from 'lucide-react';

export default function AiCopilot({ isOpen, onClose, onActionTrigger }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: 'Greetings, Officer. Sentinel Neural Copilot is online. How can I assist with statewide CCTV analysis, ANPR tracking, or tactical response dispatch?',
      timestamp: '09:42:01'
    }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const quickPrompts = [
    'Trace stolen plate GJ-01-AB-1234',
    'Identify high-speed violators on SG Highway',
    'Summarize current CCTV threat matrix',
    'Dispatch PCR unit to Vadodara Express Toll'
  ];

  const handleSend = (textToSend) => {
    const query = (textToSend || inputVal).trim();
    if (!query) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputVal('');
    setIsProcessing(true);

    setTimeout(() => {
      let aiReply = '';
      if (query.toLowerCase().includes('gj-01-ab-1234') || query.toLowerCase().includes('stolen')) {
        aiReply = '⚠️ ALERT: Vehicle GJ-01-AB-1234 (White Hyundai Verna) was last detected at CAM-001 (SG Highway Iskcon) at 09:06:12 IST moving South at 82 km/h. Nearest interception unit PCR-04 has been notified.';
      } else if (query.toLowerCase().includes('speed') || query.toLowerCase().includes('sg highway')) {
        aiReply = '📊 SG Highway Analysis: 42 vehicles clocked in the last 15 minutes. 1 overspeed violation (>70 km/h) recorded on CAM-001. Automated e-challan has been queued.';
      } else if (query.toLowerCase().includes('pcr') || query.toLowerCase().includes('dispatch')) {
        aiReply = '🚓 DISPATCH CONFIRMED: Highway Patrol Unit PCR-12 has been rerouted to Ahmedabad-Vadodara Toll Plaza (CAM-004). ETA: 4 minutes.';
      } else {
        aiReply = `Synthesized query across 1,420 CCTV streams: "${query}". Neural inference indicates normal perimeter operations with 12 active incident tickets logged statewide.`;
      }

      const aiMsg = {
        id: Date.now() + 1,
        sender: 'ai',
        text: aiReply,
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false })
      };

      setMessages((prev) => [...prev, aiMsg]);
      setIsProcessing(false);
    }, 900);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 max-w-[calc(100vw-2rem)] bg-[#080e1c]/95 backdrop-blur-xl border border-cyan-500/50 rounded-2xl shadow-2xl overflow-hidden font-mono text-xs flex flex-col h-[520px] hud-corner-box">
      
      {/* Copilot Header */}
      <div className="p-3.5 bg-gradient-to-r from-cyan-950/80 to-blue-950/80 border-b border-cyan-500/30 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/50 flex items-center justify-center text-cyan-300 shadow-glow-cyan">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-slate-100 text-xs">SENTINEL AI COPILOT</span>
              <span className="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[9px] font-bold">
                NEURAL ACTIVE
              </span>
            </div>
            <p className="text-[10px] text-cyan-400">Autonomous Threat Intelligence</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-command-card text-slate-400 hover:text-slate-200 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Message Chat Flow */}
      <div className="flex-1 p-3.5 space-y-3 overflow-y-auto">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`p-3 rounded-xl max-w-[88%] text-[11px] ${
                m.sender === 'user'
                  ? 'bg-cyan-600 text-white rounded-br-none shadow-md font-semibold'
                  : 'bg-command-card border border-command-border text-slate-200 rounded-bl-none shadow-inner'
              }`}
            >
              {m.text}
            </div>
            <span className="text-[9px] text-slate-500 mt-1 px-1">{m.timestamp}</span>
          </div>
        ))}

        {isProcessing && (
          <div className="flex items-center gap-2 text-cyan-400 text-[11px] p-2 bg-command-card rounded-lg border border-cyan-500/30 animate-pulse">
            <Sparkles className="w-3.5 h-3.5 animate-spin" />
            <span>Processing CCTV telemetry & intelligence logs...</span>
          </div>
        )}
      </div>

      {/* Fast Action Prompt Chips */}
      <div className="p-2 border-t border-command-border/60 bg-command-bg/80 overflow-x-auto no-scrollbar flex gap-1.5">
        {quickPrompts.map((prompt) => (
          <button
            key={prompt}
            onClick={() => handleSend(prompt)}
            className="px-2.5 py-1 rounded bg-command-card hover:bg-cyan-950 border border-command-border hover:border-cyan-500/60 text-slate-300 hover:text-cyan-300 text-[10px] whitespace-nowrap transition"
          >
            ⚡ {prompt}
          </button>
        ))}
      </div>

      {/* Input Query Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 border-t border-command-border/80 bg-[#060a14] flex items-center gap-2"
      >
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="Ask Sentinel Copilot or issue tactical command..."
          className="flex-1 px-3 py-2 bg-command-card border border-command-border rounded-lg text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
        />
        <button
          type="submit"
          className="p-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 text-cyan-300 transition shadow-glow-cyan"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
}
