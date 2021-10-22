import React, { useState, useEffect } from "react";
import { uniqueId } from "lodash";

export type Props = {
  position?: "top" | "bottom" | "left" | "right";
  children: React.ReactNode;
};

const Tooltip = ({ position = "right", children }: Props) => {
  const [tooltipID, setTooltipID] = useState<string | null>(null);

  useEffect(() => {
    setTooltipID(uniqueId("tooltip-"));
  }, []);

  return (
    /**
     * Using span with a11y attributes for trigger because interactive elements like <a> and <button>
     * should not be placed inside a <label> element.
     * {@link https://developer.mozilla.org/en-US/docs/Web/HTML/Element/label#accessibility_concerns}
     * Also because the <label> element raises inner events for interactive elements which causes
     * the Tooltip to show when hovering over anything inside the label instead of just the
     * tooltip trigger element.
     * The Tooltip component will be used inside a <label> element in many cases.
     */
    <span className={`tooltip tooltip--${position}`} data-testid="tooltip">
      <span
        aria-describedby={tooltipID ?? ""}
        className="tooltip__trigger"
        role="button"
        tabIndex={0}
        data-testid="tooltip-trigger"
      ></span>
      <span
        id={tooltipID ?? ""}
        className="tooltip__container"
        role="tooltip"
        data-testid="tooltip-container"
      >
        <span className="tooltip__text" data-testid="tooltip-text">
          {children}
        </span>
      </span>
    </span>
  );
};

export default Tooltip;
