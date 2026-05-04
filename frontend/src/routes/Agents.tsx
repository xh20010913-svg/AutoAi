import { Bot } from "lucide-react";

export default function Agents() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center h-full text-center">
      <Bot className="size-12 text-muted-foreground mb-4" />
      <h2 className="text-xl font-semibold tracking-tight">Agents</h2>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        Manage AI agents and their roles. Configure model tiers, token budgets,
        permissions, and task assignments for each agent in your team.
      </p>
    </div>
  );
}
