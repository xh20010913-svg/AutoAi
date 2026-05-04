import { type ReactNode, useState } from "react";

interface TooltipProps {
  content: string;
  children: ReactNode;
}

export function Tooltip({ content, children }: TooltipProps) {
  const [open, setOpen] = useState(false);

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      {children}
      {open && (
        <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 z-50 rounded-md bg-popover px-2.5 py-1.5 text-xs text-popover-foreground shadow-md border border-border whitespace-nowrap">
          {content}
        </div>
      )}
    </div>
  );
}
