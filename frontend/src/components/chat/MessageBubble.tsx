import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { WorkflowBadge } from "../workflows/WorkflowBadge";
import type { Workflow } from "../../lib/workflows";

export function MessageBubble({ role, content, workflow }: { role: "user" | "assistant"; content: string; workflow?: Workflow }) {
  return <div className={`flex gap-3 ${role === "user" ? "justify-end" : "justify-start"}`}>
    {role === "assistant" && <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-ink text-[11px] font-bold text-white">LG</div>}
    <div className={`max-w-[min(780px,88%)] ${role === "user" ? "rounded-2xl rounded-br-md bg-ink px-4 py-3 text-white" : "min-w-0 pt-1"}`}>
      {role === "assistant" && workflow && <div className="mb-3"><WorkflowBadge workflow={workflow} /></div>}
      <div className={role === "assistant" ? "markdown text-[15px] leading-7 text-slate-700" : "whitespace-pre-wrap text-[15px] leading-6"}><ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown></div>
    </div>
  </div>;
}
