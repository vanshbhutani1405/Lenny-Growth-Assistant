import { AlertCircle, Menu, PanelRight, RefreshCw, Search, ShieldCheck, Sparkles, WifiOff } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { askAgent, type AgentResponse, type Source } from "./lib/api";
import { detectWorkflow, type Workflow } from "./lib/workflows";
import { ArtifactCard } from "./components/artifacts/ArtifactCard";
import { ChatComposer } from "./components/chat/ChatComposer";
import { MessageBubble } from "./components/chat/MessageBubble";
import { Sidebar } from "./components/layout/Sidebar";
import { SourcePanel } from "./components/sources/SourcePanel";
import { WorkflowBadge } from "./components/workflows/WorkflowBadge";

type Message = { id: string; role: "user" | "assistant"; content: string; workflow?: Workflow; sources?: Source[] };
type Conversation = { id: string; sessionId: string | null; title: string; workflow: Workflow; messages: Message[] };

const storageKey = "lenny-growth-session";
const historyKey = "lenny-growth-conversations";

export default function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(() => localStorage.getItem(storageKey));
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>(() => { try { return JSON.parse(localStorage.getItem(historyKey) ?? "[]"); } catch { return []; } });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusIndex, setStatusIndex] = useState(0);
  const statusLabels = ["Searching Lenny's episodes...", "Analyzing evidence...", "Writing answer..."];
  useEffect(() => { localStorage.setItem(historyKey, JSON.stringify(conversations)); }, [conversations]);

  const activeWorkflow = useMemo(() => conversation?.workflow ?? "grounded_qa", [conversation]);
  const send = async (query: string) => {
    const workflow = detectWorkflow(query);
    const userMessage: Message = { id: crypto.randomUUID(), role: "user", content: query, workflow };
    const nextConversation = conversation ?? { id: crypto.randomUUID(), sessionId: null, title: query, workflow, messages: [] };
    setConversation({ ...nextConversation, workflow, messages: [...nextConversation.messages, userMessage] });
    setConversations((items) => [
      { ...nextConversation, workflow, title: nextConversation.messages.length ? nextConversation.title : query, messages: [...nextConversation.messages, userMessage] },
      ...items.filter((item) => item.id !== nextConversation.id),
    ]);
    setLoading(true); setError(null); setStatusIndex(0);
    const timer = window.setInterval(() => setStatusIndex((index) => (index + 1) % statusLabels.length), 1400);
    try {
      const result: AgentResponse = await askAgent(query, sessionId ?? undefined);
      setSessionId(result.session_id); localStorage.setItem(storageKey, result.session_id);
      const assistantMessage: Message = { id: crypto.randomUUID(), role: "assistant", content: result.answer, workflow, sources: result.sources };
      setConversation((current) => current ? { ...current, sessionId: result.session_id, messages: [...current.messages, assistantMessage] } : current);
      setConversations((items) => items.map((item) => item.id === nextConversation.id ? { ...item, sessionId: result.session_id, messages: [...item.messages, assistantMessage] } : item));
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "The backend is unavailable.";
      setError(message);
    } finally { window.clearInterval(timer); setLoading(false); }
  };

  const newConversation = () => { setConversation(null); setSessionId(null); localStorage.removeItem(storageKey); setError(null); };
  const selectConversation = (id: string) => { const selected = conversations.find((item) => item.id === id); if (!selected) return; setConversation(selected); setSessionId(selected.sessionId); if (selected.sessionId) localStorage.setItem(storageKey, selected.sessionId); };
  const startSuggestion = (query: string) => void send(query);

  return <div className="flex h-screen overflow-hidden bg-paper text-ink">
    <Sidebar collapsed={collapsed} onCollapse={() => setCollapsed(!collapsed)} onNew={newConversation} onSelect={selectConversation} conversations={conversations} activeId={conversation?.id ?? null} />
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="flex h-20 shrink-0 items-center justify-between border-b border-line bg-white/80 px-5 backdrop-blur md:px-9"><div className="flex items-center gap-3"><button className="rounded-lg p-2 text-slate-400 hover:bg-slate-50 md:hidden"><Menu size={19} /></button><div><div className="text-[11px] font-bold uppercase tracking-[.16em] text-slate-400">Knowledge workspace</div><h1 className="mt-1 text-lg font-bold tracking-[-.03em]">Ask better questions</h1></div></div><div className="hidden items-center gap-3 sm:flex"><span className="inline-flex items-center gap-1.5 text-xs text-slate-500"><span className="h-2 w-2 rounded-full bg-emerald-500" />Local knowledge base ready</span><button className="rounded-lg border border-line p-2 text-slate-400 hover:bg-slate-50 hover:text-ink" aria-label="Workspace panel"><PanelRight size={16} /></button></div></header>
      <div className="flex min-h-0 flex-1 flex-col"><div className="flex-1 overflow-y-auto"><div className="mx-auto w-full max-w-4xl px-5 pb-10 pt-10 md:px-10 md:pt-14">
        {!conversation ? <Welcome onSuggestion={startSuggestion} /> : <div className="space-y-8">{conversation.messages.map((message) => <div key={message.id}><MessageBubble role={message.role} content={message.content} workflow={message.workflow} />{message.role === "assistant" && message.sources && <><SourcePanel sources={message.sources} />{message.workflow === "ship30" && <ArtifactCard content={message.content} />}</>}</div>)}{loading && <div className="flex items-center gap-3 text-sm text-muted"><div className="flex gap-1"><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500" /><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500 [animation-delay:120ms]" /><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500 [animation-delay:240ms]" /></div>{statusLabels[statusIndex]}</div>}</div>}
        {error && <ErrorState message={error} onRetry={() => setError(null)} />}
      </div></div><div className="border-t border-line bg-paper/90 px-5 pb-5 pt-4 md:px-10"><div className="mx-auto max-w-4xl"><div className="mb-2 flex items-center justify-between text-[11px] text-slate-400"><span className="inline-flex items-center gap-1.5"><ShieldCheck size={13} />Answers are grounded in transcript evidence</span><span className="hidden sm:inline">Enter to send · Shift+Enter for new line</span></div><ChatComposer disabled={loading} onSend={send} /></div></div></div>
    </main>
  </div>;
}

function Welcome({ onSuggestion }: { onSuggestion: (query: string) => void }) {
  const suggestions = ["What does Lenny say about product-market fit?", "Research the common patterns behind successful growth loops", "Write a Ship 30 essay about finding product-market fit"];
  return <div className="flex min-h-[55vh] flex-col justify-center"><div className="mb-8"><div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-[0_8px_24px_rgba(37,99,235,.2)]"><Sparkles size={23} /></div><p className="mb-2 text-sm font-semibold text-blue-600">Lenny Growth Assistant</p><h2 className="max-w-xl text-4xl font-bold leading-[1.1] tracking-[-.055em] text-ink md:text-5xl">Good growth advice,<br /><span className="text-slate-400">when you need it.</span></h2><p className="mt-5 max-w-lg text-[15px] leading-7 text-muted">Ask questions across Lenny’s podcast transcripts, synthesize the thinking, or turn an insight into something worth sharing.</p></div><div className="grid gap-2 sm:grid-cols-3">{suggestions.map((suggestion) => <button key={suggestion} onClick={() => onSuggestion(suggestion)} className="group rounded-xl border border-line bg-white p-3.5 text-left text-xs leading-5 text-slate-600 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-soft"><span className="mb-2 block text-slate-300 transition group-hover:text-blue-500"><Search size={15} /></span>{suggestion}</button>)}</div></div>;
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  const isOffline = /unavailable|ollama|backend|provider/i.test(message);
  return <div className="mt-6 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-800"><div className="mt-0.5 rounded-lg bg-white/70 p-1.5">{isOffline ? <WifiOff size={16} /> : <AlertCircle size={16} />}</div><div className="flex-1"><div className="font-semibold">{isOffline ? "The assistant is temporarily unavailable" : "Something went wrong"}</div><div className="mt-1 text-xs leading-5 text-red-700/80">{message}</div></div><button onClick={onRetry} className="inline-flex items-center gap-1 text-xs font-semibold text-red-700 hover:underline"><RefreshCw size={12} />Dismiss</button></div>;
}
