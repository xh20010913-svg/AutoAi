import { Settings as SettingsIcon } from "lucide-react";
import ThemeToggle from "@/components/theme/ThemeToggle";

export default function Settings() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center h-full text-center">
      <SettingsIcon className="size-12 text-muted-foreground mb-4" />
      <h2 className="text-xl font-semibold tracking-tight">Settings</h2>
      <p className="mt-2 text-sm text-muted-foreground max-w-md mb-6">
        Application preferences, theme selection, project configuration, and
        agent runtime settings.
      </p>
      <ThemeToggle />
    </div>
  );
}
