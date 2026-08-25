import { ChevronDown, ExternalLink, FileText, Quote } from "lucide-react";
import { useState } from "react";
import type { Source } from "../../lib/api";

export function SourcePanel({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return <section className="mt-5 border-t border-line pt-5"><div className="mb-3 flex items-center gap-2"><Quote size={15} className="text-blue-600" /><h3 className="text-xs font-bold uppercase tracking-[.14em] text-slate-500">Evidence from Lenny's episodes</h3><span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">{sources.length}</span></div><div className="grid gap-2">{sources.map((source) => <SourceCard key={source.chunk_id} source={source} />)}</div></section>;
}

function SourceCard({ source }: { source: Source }) {
  const [open, setOpen] = useState(false);
  return <div className="rounded-xl border border-line bg-white transition hover:border-slate-300"><div className="flex items-start gap-3 p-3"><div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600"><FileText size={14} /></div><div className="min-w-0 flex-1"><div className="flex items-start justify-between gap-3"><div><div className="truncate text-sm font-semibold text-ink">{source.title || source.episode_slug}</div><div className="mt-0.5 text-xs text-muted">{source.guest || "Unknown guest"} · {source.episode_slug}</div></div><div className="shrink-0 rounded-md bg-emerald-50 px-2 py-1 text-[10px] font-bold text-emerald-700">{(source.similarity_score * 100).toFixed(0)}% match</div></div><div className="mt-2 flex flex-wrap items-center gap-3 text-[10px] text-slate-400"><span>Chunk {source.chunk_index}</span><span>{source.chunk_id.slice(0, 12)}…</span>{source.youtube_url && <a href={source.youtube_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-blue-600 hover:underline">Watch episode <ExternalLink size={10} /></a>}</div></div><button aria-label="Toggle transcript evidence" onClick={() => setOpen(!open)} className="mt-1 rounded-md p-1 text-slate-400 hover:bg-slate-50 hover:text-ink"><ChevronDown size={15} className={`transition ${open ? "rotate-180" : ""}`} /></button></div>{open && source.evidence && <div className="border-t border-line bg-slate-50/70 px-4 py-3 text-xs leading-5 text-slate-600">“{source.evidence}”</div>}</div>;
}
