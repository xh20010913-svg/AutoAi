import { Sun, Moon, Monitor } from "lucide-react";
import { useTheme, type Theme } from "@/components/theme/ThemeProvider";
import { cn } from "@/lib/utils";

const icons: Record<Theme, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};

const next: Record<Theme, Theme> = {
  light: "dark",
  dark: "system",
  system: "light",
};

const labels: Record<Theme, string> = {
  light: "Light",
  dark: "Dark",
  system: "System",
};

interface ThemeToggleProps {
  className?: string;
}

export default function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  const Icon = icons[theme];

  return (
    <button
      onClick={() => setTheme(next[theme])}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium",
        "text-muted-foreground hover:text-foreground hover:bg-accent transition-colors",
        className
      )}
      title={`Theme: ${labels[theme]}`}
    >
      <Icon className="size-4" />
      <span>{labels[theme]}</span>
    </button>
  );
}
