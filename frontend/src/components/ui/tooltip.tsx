import { Tooltip as TooltipPrimitive } from "@base-ui/react/tooltip"
import { mergeProps } from "@base-ui/react/merge-props"
import { useRender } from "@base-ui/react/use-render"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const tooltipVariants = cva(
  "z-50 max-w-xs rounded-lg border border-border bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md",
  {
    variants: {
      side: {
        top: "mb-1",
        right: "ml-1",
        bottom: "mt-1",
        left: "mr-1",
      },
    },
    defaultVariants: {
      side: "top",
    },
  }
)

function Tooltip(props: TooltipPrimitive.Root.Props) {
  return <TooltipPrimitive.Root {...props} />
}

function TooltipTrigger({
  className,
  render,
  ...props
}: useRender.ComponentProps<"button">) {
  return useRender({
    defaultTagName: "button",
    props: mergeProps<"button">({ className: cn("cursor-pointer", className) }, props),
    render,
  })
}

function TooltipContent({
  className,
  side = "top",
  render,
  ...props
}: useRender.ComponentProps<"div"> & {
  side?: "top" | "right" | "bottom" | "left"
}) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Positioner side={side} align="center">
        <TooltipPrimitive.Popup
          render={
            <div
              className={cn(tooltipVariants({ side }), className)}
              {...props}
            />
          }
        />
      </TooltipPrimitive.Positioner>
    </TooltipPrimitive.Portal>
  )
}

export { Tooltip, TooltipTrigger, TooltipContent, tooltipVariants }
