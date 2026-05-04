import { forwardRef, type ButtonHTMLAttributes } from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border-2",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground border-primary hover:opacity-90 pixel-border-sm",
        destructive: "bg-destructive text-destructive-foreground border-destructive hover:opacity-90",
        outline: "border-border bg-transparent hover:bg-accent hover:text-accent-foreground",
        ghost: "border-transparent hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground border-secondary hover:opacity-90",
      },
      size: {
        default: "h-8 px-3 py-1.5",
        sm: "h-7 px-2",
        lg: "h-9 px-4",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
