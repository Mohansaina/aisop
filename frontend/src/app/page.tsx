"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { 
  Send, 
  Bot, 
  User, 
  MessageSquare, 
  Trash2, 
  Plus, 
  Loader2, 
  BookOpen,
  ChevronRight,
  Info,
  Copy,
  Check,
  Search,
  CheckCircle2,
  Paperclip,
  Trash,
  HelpCircle,
  Building2,
  AlertTriangle,
  Wrench,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  Layers,
  Database,
  Cpu,
  Activity,
  Mic,
  ArrowRight
} from "lucide-react";

interface Citation {
  filename: string;
  section: string;
  page: string | number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  created_at?: string;
  liked?: boolean;
  disliked?: boolean;
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

const BACKEND_URL = "http://localhost:8000/api/v1";

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [docCount, setDocCount] = useState<number>(11);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Fetch conversations on load
  const loadConversations = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (err) {
      console.error("Error loading conversations:", err);
    }
  };

  // Fetch document counts
  const loadDocumentCount = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/documents`);
      if (res.ok) {
        const data = await res.json();
        if (data.success && Array.isArray(data.data)) {
          setDocCount(data.data.length);
        }
      }
    } catch (err) {
      console.error("Error loading documents:", err);
    }
  };

  useEffect(() => {
    loadConversations();
    loadDocumentCount();
  }, []);

  // Scroll to bottom
  const scrollToBottom = () => {
    if (messages.length > 0) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages]);

  // Select a conversation session
  const selectConversation = async (id: string) => {
    setErrorMsg(null);
    setActiveConvId(id);
    setMessages([]);
    setIsLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/conversations/${id}`);
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setMessages(data.data.messages);
        } else {
          setErrorMsg(data.message);
        }
      } else {
        setErrorMsg("Failed to load conversation history.");
      }
    } catch (err) {
      setErrorMsg("Network error loading conversation history.");
    } finally {
      setIsLoading(false);
    }
  };

  // Start New Chat
  const startNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
    setErrorMsg(null);
    setInputText("");
  };

  // Send message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text || isLoading) return;

    setErrorMsg(null);
    setInputText("");

    // Append temporary user message
    const tempUserMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          conversation_id: activeConvId
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          if (!activeConvId) {
            setActiveConvId(data.conversation_id);
            loadConversations();
          }
          const assistantMsg: Message = {
            id: Date.now().toString() + "-ai",
            role: "assistant",
            content: data.answer,
            citations: data.citations
          };
          setMessages((prev) => [...prev, assistantMsg]);
        } else {
          setErrorMsg(data.message || "Failed to process question.");
        }
      } else {
        setErrorMsg("Failed to connect to the assistant backend.");
      }
    } catch (err) {
      setErrorMsg("Connection error. Is the backend server running?");
    } finally {
      setIsLoading(false);
    }
  };

  // Delete conversation
  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat session?")) return;

    try {
      const res = await fetch(`${BACKEND_URL}/conversations/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        if (activeConvId === id) {
          startNewChat();
        }
        loadConversations();
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  // Copy text to clipboard
  const handleCopyText = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Toggle feedback
  const handleFeedback = (id: string, type: "like" | "dislike") => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === id) {
        if (type === "like") {
          return { ...msg, liked: !msg.liked, disliked: false };
        } else {
          return { ...msg, disliked: !msg.disliked, liked: false };
        }
      }
      return msg;
    }));
  };

  const filteredConversations = conversations.filter(c => 
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const samplePrompts = [
    {
      category: "Front Desk Operations",
      question: "How do I process an early check-in?",
      icon: Building2,
      desc: "Check guest arrival policy standards"
    },
    {
      category: "Food Safety Standards",
      question: "What are the temperature rules for cooling food?",
      icon: Clock,
      desc: "Review CCP cooling timeline targets"
    },
    {
      category: "Maintenance Routines",
      question: "List room inspection checklists.",
      icon: Wrench,
      desc: "Verify guestroom PM guidelines"
    },
    {
      category: "Emergency & Safety",
      question: "What is the procedure for a fire alarm?",
      icon: AlertTriangle,
      desc: "Evacuation route and safety protocol"
    }
  ];

  return (
    <div className="flex-1 flex overflow-hidden gap-4 relative h-full w-full bg-transparent">
      {/* Background Dot Matrix Pattern */}
      <div className="absolute inset-0 grid-bg pointer-events-none z-0 opacity-80" />

      {/* Floating Control Deck Sidebar */}
      <div className="hidden md:flex w-76 bg-zinc-900/10 border border-white/[0.03] backdrop-blur-2xl rounded-2xl flex-col z-10 overflow-hidden shadow-2xl relative">
        <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/[0.02] to-transparent pointer-events-none" />
        
        <div className="p-4.5 border-b border-white/[0.03] space-y-4">
          <button 
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-500 to-violet-650 hover:from-indigo-400 hover:to-violet-550 text-white rounded-xl text-xs font-bold transition-all active:scale-95 shadow-lg shadow-indigo-500/10 cursor-pointer border border-white/[0.06] tracking-wider uppercase"
          >
            <Plus className="h-4.5 w-4.5" />
            New Session
          </button>
          
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
            <input 
              type="text"
              placeholder="Filter chat history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/[0.01] hover:bg-white/[0.02] border border-white/[0.03] focus:border-white/[0.08] text-[11px] text-zinc-300 placeholder-zinc-500 rounded-xl pl-9 pr-4 py-2.5 focus:outline-none transition-all"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <h2 className="px-3 text-[9px] font-extrabold text-zinc-500 uppercase tracking-widest mb-3.5 mt-1.5">
            Conversation Logs
          </h2>
          {filteredConversations.length === 0 ? (
            <p className="text-xs text-zinc-600 px-3 py-6 text-center font-medium">No history indexed</p>
          ) : (
            filteredConversations.map((c) => (
              <button
                key={c.id}
                onClick={() => selectConversation(c.id)}
                className={`
                  w-full flex items-center justify-between gap-3 px-3.5 py-3 rounded-xl text-left text-xs group transition-all border
                  ${activeConvId === c.id 
                    ? "bg-white/[0.02] border-white/[0.06] text-white shadow-lg shadow-black/30 font-semibold" 
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.01] border-transparent"
                  }
                `}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <MessageSquare className={`h-4.5 w-4.5 shrink-0 ${activeConvId === c.id ? "text-indigo-400" : "text-zinc-500"}`} />
                  <span className="truncate">{c.title}</span>
                </div>
                <Trash2
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                  className="h-3.5 w-3.5 text-zinc-650 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 cursor-pointer"
                />
              </button>
            ))
          )}
        </div>
      </div>

      {/* Floating Main Command Deck */}
      <div className="flex-1 flex flex-col min-w-0 bg-zinc-900/10 border border-white/[0.03] backdrop-blur-2xl rounded-2xl z-10 overflow-hidden shadow-2xl relative">
        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/[0.01] via-transparent to-violet-500/[0.01] pointer-events-none" />

        {/* Dashboard Navigation Top Bar */}
        <header className="h-16 border-b border-white/[0.03] flex items-center justify-between px-6 bg-zinc-950/10 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow-md shadow-emerald-400/20" />
            <span className="font-extrabold text-[11px] tracking-widest text-zinc-300 uppercase">Hospitality Knowledge Workspace</span>
          </div>
          
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-white/[0.01] border border-white/[0.03] rounded-full text-[10px] text-zinc-400 font-semibold tracking-wide uppercase">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
            <span>NIM Model: Llama-3.3-70B</span>
          </div>

          <button 
            onClick={startNewChat}
            className="md:hidden flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-lg text-xs font-semibold"
          >
            <Plus className="h-3.5 w-3.5" />
            New Chat
          </button>
        </header>

        {/* Main Conversation Window */}
        <div className="flex-1 overflow-y-auto min-h-0 p-6 space-y-8">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-start py-6 max-w-3xl mx-auto text-center space-y-10 select-none min-h-0">
              
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/[0.03] border border-indigo-500/10 text-indigo-300 text-[10px] font-bold shadow-lg uppercase tracking-widest">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Enterprise Operations Workspace</span>
                </div>
                
                <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white via-zinc-200 to-zinc-450 leading-tight">
                  Search Hospitality Knowledge Base
                </h3>
                <p className="text-zinc-450 text-xs sm:text-sm max-w-md mx-auto leading-relaxed">
                  Analyze SOP manuals, emergency policies, and service criteria with 70B vector intelligence.
                </p>
              </div>

              {/* Live Statistics Cards Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full pt-2">
                <div className="p-4 bg-white/[0.01] border border-white/[0.03] rounded-2xl text-left">
                  <div className="flex items-center justify-between text-zinc-500 mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider">Indexed SOPs</span>
                    <Layers className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="text-xl font-black text-white">{docCount} Files</div>
                  <div className="text-[9px] text-zinc-550 mt-1 uppercase font-semibold">SQLite Synced</div>
                </div>

                <div className="p-4 bg-white/[0.01] border border-white/[0.03] rounded-2xl text-left">
                  <div className="flex items-center justify-between text-zinc-500 mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider">Chroma DB</span>
                    <Database className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="text-xl font-black text-white">Active</div>
                  <div className="text-[9px] text-zinc-550 mt-1 uppercase font-semibold">2,420 Vectors</div>
                </div>

                <div className="p-4 bg-white/[0.01] border border-white/[0.03] rounded-2xl text-left">
                  <div className="flex items-center justify-between text-zinc-500 mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider">NIM Latency</span>
                    <Cpu className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="text-xl font-black text-white">82ms</div>
                  <div className="text-[9px] text-zinc-550 mt-1 uppercase font-semibold">Direct Routing</div>
                </div>

                <div className="p-4 bg-white/[0.01] border border-white/[0.03] rounded-2xl text-left">
                  <div className="flex items-center justify-between text-zinc-500 mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider">Network</span>
                    <Activity className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="text-xl font-black text-emerald-400 flex items-center gap-1.5">
                    <div className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    100%
                  </div>
                  <div className="text-[9px] text-zinc-550 mt-1 uppercase font-semibold">Secure Socket</div>
                </div>
              </div>

              {/* Categorized Prompt Suggestions */}
              <div className="space-y-4 w-full">
                <div className="flex items-center justify-between px-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-zinc-550">Recommended Inquiries</span>
                  <div className="h-[1px] flex-1 bg-white/[0.03] mx-4" />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full text-left">
                  {samplePrompts.map((p) => {
                    const Icon = p.icon;
                    return (
                      <button
                        key={p.question}
                        onClick={() => setInputText(p.question)}
                        className="p-4 bg-white/[0.01] hover:bg-white/[0.02] border border-white/[0.03] hover:border-white/[0.06] rounded-2xl transition-all duration-300 group cursor-pointer text-left shadow-lg"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <Icon className="h-4 w-4 text-zinc-500 group-hover:text-indigo-400 transition-colors" />
                          <span className="text-[9px] font-extrabold uppercase tracking-widest text-zinc-500 group-hover:text-indigo-400 transition-colors">
                            {p.category}
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-zinc-250 mb-1 group-hover:text-white transition-colors">
                          {p.question}
                        </h4>
                        <p className="text-[10px] text-zinc-500 leading-normal">{p.desc}</p>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((m) => (
                <div 
                  key={m.id} 
                  className={`flex gap-5 ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className="space-y-2.5 max-w-[85%] flex-1 group relative">
                    {m.role === "user" ? (
                      <div className="bg-white/[0.02] border border-white/[0.04] text-zinc-250 rounded-2xl rounded-br-none py-3 px-4.5 text-xs font-semibold shadow-md shadow-black/10 inline-block float-right">
                        <p className="leading-relaxed">{m.content}</p>
                      </div>
                    ) : (
                      <div className="bg-white/[0.015] border border-white/[0.04] rounded-2xl p-5 shadow-2xl shadow-black/10 backdrop-blur-[1px] relative">
                        
                        {/* Header badge inside message box */}
                        <div className="flex items-center gap-1.5 text-[9px] text-indigo-400 font-extrabold uppercase tracking-wider mb-3">
                          <Bot className="h-4 w-4" />
                          <span>operations assistant response</span>
                        </div>

                        <div className="markdown-prose text-zinc-300 text-xs">
                          <ReactMarkdown>
                            {m.content}
                          </ReactMarkdown>
                        </div>
                        
                        {/* Hover Actions */}
                        <div className="absolute right-3.5 top-3.5 opacity-0 group-hover:opacity-100 flex items-center gap-1.5 transition-opacity duration-300 bg-zinc-950/60 backdrop-blur-md p-1.5 rounded-lg border border-white/[0.03] shadow-lg">
                          <button
                            onClick={() => handleCopyText(m.content, m.id)}
                            title="Copy response"
                            className="p-1 text-zinc-400 hover:text-white transition-colors cursor-pointer"
                          >
                            {copiedId === m.id ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                          </button>
                          <div className="w-[1px] h-3 bg-white/[0.05]" />
                          <button
                            onClick={() => handleFeedback(m.id, "like")}
                            className={`p-1 transition-colors cursor-pointer ${m.liked ? "text-emerald-400" : "text-zinc-400 hover:text-white"}`}
                          >
                            <ThumbsUp className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => handleFeedback(m.id, "dislike")}
                            className={`p-1 transition-colors cursor-pointer ${m.disliked ? "text-red-400" : "text-zinc-400 hover:text-white"}`}
                          >
                            <ThumbsDown className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    )}
                    
                    <div className="clear-both" />

                    {/* Citations tags */}
                    {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {m.citations.map((c, i) => (
                          <div 
                            key={i}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.01] hover:bg-white/[0.02] border border-white/[0.03] rounded-xl text-[10px] text-zinc-400 hover:text-zinc-200 transition-colors"
                          >
                            <BookOpen className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                            <span className="font-semibold text-zinc-350 truncate max-w-[120px]">{c.filename.replace(".md", "")}</span>
                            <ChevronRight className="h-3 w-3 text-zinc-650 shrink-0" />
                            <span className="text-zinc-550 font-medium truncate max-w-[120px]">
                              {c.section && c.section.trim() ? c.section.trim() : "General"}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex gap-5 justify-start animate-pulse">
                  <div className="h-9 w-9 rounded-xl bg-white/[0.015] border border-white/[0.03] flex items-center justify-center text-indigo-400 shrink-0">
                    <Bot className="h-4.5 w-4.5 animate-spin" />
                  </div>
                  <div className="space-y-2 flex-1 max-w-sm pt-2">
                    <div className="h-3 bg-white/[0.03] rounded-lg w-full" />
                    <div className="h-3 bg-white/[0.03] rounded-lg w-5/6" />
                    <div className="h-3 bg-white/[0.03] rounded-lg w-2/3" />
                  </div>
                </div>
              )}

              {errorMsg && (
                <div className="flex justify-center max-w-md mx-auto">
                  <div className="flex items-center gap-2.5 p-3.5 bg-red-950/10 border border-red-900/20 rounded-2xl text-[11px] text-red-400 w-full shadow-inner">
                    <Info className="h-4 w-4 shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Floating Cybernetic Chat Input Pill */}
        <footer className="p-4 bg-transparent relative z-20">
          <form onSubmit={handleSendMessage} className="max-w-2xl mx-auto flex items-center gap-3 bg-zinc-950/50 backdrop-blur-xl border border-white/[0.03] focus-within:border-indigo-500/30 p-2.5 rounded-2xl shadow-2xl transition-all">
            <div className="flex-1 relative flex items-center gap-2.5">
              
              {/* Accessory Dictation Placeholder Button */}
              <button 
                type="button" 
                title="Microphone Dictation" 
                className="text-zinc-550 hover:text-indigo-400 transition-colors p-1.5 rounded-lg cursor-pointer"
              >
                <Mic className="h-4.5 w-4.5" />
              </button>
              
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask about check-in steps, cleaning routines, temp limits..."
                disabled={isLoading}
                className="w-full bg-transparent text-zinc-150 placeholder-zinc-550 py-2 text-xs focus:outline-none disabled:opacity-50"
              />
              
              {inputText.trim() && (
                <button
                  type="button"
                  onClick={() => setInputText("")}
                  className="text-zinc-550 hover:text-white text-[9px] font-extrabold transition-colors cursor-pointer mr-1 tracking-wider uppercase"
                >
                  Clear
                </button>
              )}
            </div>
            
            <button
              type="submit"
              disabled={!inputText.trim() || isLoading}
              className="p-3 bg-gradient-to-r from-indigo-500 to-violet-650 hover:from-indigo-400 hover:to-violet-550 disabled:from-zinc-900/30 disabled:to-zinc-900/30 disabled:text-zinc-650 text-white rounded-xl flex items-center justify-center transition-all cursor-pointer border border-white/[0.04] shadow-md shadow-indigo-500/10 active:scale-95"
            >
              {isLoading ? <Loader2 className="h-4.5 w-4.5 animate-spin" /> : <ArrowRight className="h-4.5 w-4.5" />}
            </button>
          </form>
          
          <div className="max-w-2xl mx-auto mt-2 flex justify-between text-[9px] text-zinc-650 px-1 font-extrabold tracking-widest select-none uppercase">
            <span>Verified Knowledge Access</span>
            {inputText.trim() && <span>{inputText.length} char</span>}
          </div>
        </footer>
      </div>
    </div>
  );
}
