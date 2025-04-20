import type * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "bg-[#58a6ff] text-[#0d1117] hover:bg-[#58a6ff]/90",
        secondary: "bg-[#161b22] text-[#c9d1d9] hover:bg-[#161b22]/80",
        destructive: "bg-[#f85149] text-[#0d1117] hover:bg-[#f85149]/90",
        outline: "border border-[#30363d] text-[#8b949e]",
        success: "bg-[#3fb950]/20 text-[#3fb950] border border-[#3fb950]/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
