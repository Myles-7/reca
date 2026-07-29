import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const content =
    variant === "responsive" ? (
      <span className={cn("font-semibold group-data-[collapsible=icon]:hidden", className)}>
        RECA
      </span>
    ) : (
      <span className={cn(variant === "full" ? "font-semibold" : "font-bold", className)}>
        RECA
      </span>
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
