import { Copy, Download, FileText } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function ArtifactCard({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => { await navigator.clipboard?.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1600); };
  const download = () => { const blob = new Blob([content], { type: "text/markdown" }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "lenny-growth-draft.md"; link.click(); URL.revokeObjectURL(url); };
  return <div className="mt-5 overflow-hidden rounded-2xl border border-line bg-white shadow-soft"><div className="flex items-center justify-between border-b border-line bg-slate-50/70 px-4 py-3"><div className="flex items-center gap-2"><FileText size={15} className="text-amber-600" /><span className="text-xs font-bold uppercase tracking-[.13em] text-slate-500">Ship 30 draft</span><span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-500">Transcript-backed</span></div><div className="flex gap-1"><button onClick={copy} className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-500 hover:bg-white hover:text-ink"><Copy size={13} />{copied ? "Copied" : "Copy"}</button><button onClick={download} className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-500 hover:bg-white hover:text-ink"><Download size={13} />Download</button></div></div><div className="markdown max-h-[600px] overflow-y-auto p-6 text-[15px] leading-7 text-slate-700"><ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown></div></div>;
}
