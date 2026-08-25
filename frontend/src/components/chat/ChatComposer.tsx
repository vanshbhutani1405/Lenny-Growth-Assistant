import { ArrowUp, Paperclip } from "lucide-react";
import { useState } from "react";

export function ChatComposer({ disabled, onSend }: { disabled: boolean; onSend: (value: string) => void }) {
  const [value, setValue] = useState("");
  const submit = () => { const next = value.trim(); if (!next || disabled) return; onSend(next); setValue(""); };
  return <div className="rounded-2xl border border-line bg-white p-2 shadow-soft"><textarea value={value} disabled={disabled} onChange={(event) => setValue(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(); } }} placeholder="Ask Lenny about product, growth, or your next essay..." rows={3} className="w-full resize-none border-0 bg-transparent px-3 py-2 text-sm leading-6 text-ink outline-none placeholder:text-slate-400 disabled:opacity-60" /><div className="flex items-center justify-between px-2 pb-1"><button className="rounded-lg p-2 text-slate-400 hover:bg-slate-50 hover:text-ink" aria-label="Attach file"><Paperclip size={17} /></button><button onClick={submit} disabled={disabled || !value.trim()} className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink text-white transition hover:bg-[#263551] disabled:cursor-not-allowed disabled:bg-slate-200"><ArrowUp size={17} /></button></div></div>;
}
