import { BookOpen, FileText, Sparkles } from "lucide-react";
import { workflowMeta, type Workflow } from "../../lib/workflows";

const icons = { grounded_qa: BookOpen, research_synthesis: Sparkles, ship30: FileText };

export function WorkflowBadge({ workflow }: { workflow: Workflow }) {
  const meta = workflowMeta[workflow];
  const Icon = icons[workflow];
  return <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${meta.tone}`}><Icon size={13} />{meta.label}</span>;
}
