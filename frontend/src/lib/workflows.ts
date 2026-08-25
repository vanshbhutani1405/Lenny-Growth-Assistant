export type Workflow = "grounded_qa" | "research_synthesis" | "ship30";

export function detectWorkflow(query: string): Workflow {
  const text = query.toLowerCase();
  if (["ship 30", "ship30", "essay", "newsletter", "write a post", "blog post"].some((term) => text.includes(term))) return "ship30";
  if (["research", "synthesize", "compare", "contrast", "patterns", "themes", "across episodes", "summarize the advice"].some((term) => text.includes(term))) return "research_synthesis";
  return "grounded_qa";
}

export const workflowMeta: Record<Workflow, { label: string; description: string; tone: string }> = {
  grounded_qa: { label: "Grounded Q&A", description: "Transcript-backed answer", tone: "bg-blue-50 text-blue-700 border-blue-100" },
  research_synthesis: { label: "Research & Synthesis", description: "Themes across the corpus", tone: "bg-violet-50 text-violet-700 border-violet-100" },
  ship30: { label: "Ship 30", description: "Essay drafting workflow", tone: "bg-amber-50 text-amber-700 border-amber-100" },
};
