import React, { useEffect } from "react";
import Icon from "./Icon";

// Only load USWDS tooltip JS on client-side since it
// references `window`, which isn't available during
// the Node.js-based build process ("server-side")
let tooltip: {
  on: () => void;
  off: () => void;
} | null = null;
if (typeof window !== "undefined") {
  tooltip = require("uswds/src/js/components/tooltip");
}

interface TooltipIconProps {
  children: string;
  position?: "top" | "bottom" | "left" | "right";
}

const TooltipIcon = (props: TooltipIconProps) => {
  const position = props.position;

  useEffect(() => {
    if (tooltip) tooltip.on();

    return () => {
      if (tooltip) tooltip.off();
    };
  });

  return (
    <div
      data-position={position}
      data-classes="text-normal"
      className="usa-tooltip display-inline-block padding-05 text-middle text-base-dark"
      title={props.children}
    >
      <Icon name="info" />
      {/* A little hacky, but this text element makes VoiceOver read the tooltip text. */}
      <span className="usa-sr-only">tip:</span>
    </div>
  );
};

export default TooltipIcon;
