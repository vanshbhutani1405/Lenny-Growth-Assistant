import { BookOpen, ChevronLeft, ChevronRight, Clock3, MessageSquarePlus, Radio } from "lucide-react";
import { workflowMeta, type Workflow } from "../../lib/workflows";

type Conversation = { id: string; title: string; workflow: Workflow };

export function Sidebar({ collapsed, onCollapse, onNew, onSelect, conversations, activeId }: { collapsed: boolean; onCollapse: () => void; onNew: () => void; onSelect: (conversationId: string) => void; conversations: Conversation[]; activeId: string | null }) {
  return <aside className={`relative flex shrink-0 flex-col border-r border-line bg-white transition-all duration-200 ${collapsed ? "w-[72px]" : "w-[280px]"}`}>
    <div className="flex h-20 items-center gap-3 border-b border-line px-5">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-ink text-white shadow-soft"><BookOpen size={18} /></div>
      {!collapsed && <div><div className="text-sm font-bold tracking-[-.02em]">Lenny Growth</div><div className="text-[11px] text-muted">Assistant</div></div>}
    </div>
    <div className="p-4"><button onClick={onNew} className={`flex w-full items-center justify-center gap-2 rounded-xl bg-ink px-3 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#263551] ${collapsed ? "px-0" : ""}`}><MessageSquarePlus size={17} />{!collapsed && "New conversation"}</button></div>
    {!collapsed && <>
      <div className="px-5 pb-2 text-[10px] font-bold uppercase tracking-[.16em] text-slate-400">Recent conversations</div>
      <div className="flex-1 space-y-1 overflow-y-auto px-3">
        {conversations.length === 0 ? <div className="rounded-xl border border-dashed border-line px-3 py-5 text-center text-xs leading-5 text-muted">Your conversations will appear here.</div> : conversations.map((conversation) => <button key={conversation.id} onClick={() => onSelect(conversation.id)} className={`w-full rounded-xl px-3 py-2.5 text-left ${activeId === conversation.id ? "bg-slate-100" : "hover:bg-slate-50"}`}><div className="truncate text-sm font-medium">{conversation.title}</div><div className="mt-1 flex items-center gap-1.5 text-[10px] text-muted"><Radio size={10} />{workflowMeta[conversation.workflow].label}</div></button>)}
      </div>
      <div className="mt-auto border-t border-line p-4 text-[11px] text-muted"><div className="flex items-center gap-2"><Clock3 size={13} />Sessions are kept locally</div></div>
    </>}
    <button aria-label="Collapse sidebar" onClick={onCollapse} className="absolute -right-3 top-[76px] flex h-6 w-6 items-center justify-center rounded-full border border-line bg-white text-muted shadow-sm hover:text-ink">{collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}</button>
  </aside>;
}
