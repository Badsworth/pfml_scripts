import React from "react";
import classnames from "classnames";

interface IconProps {
  /** Name of the the USWDS Icon to render */
  name: string;
  className?: string;
  fill?: string;
  size?: number;
}
/**
 * SVG icon from the U.S. Web Design System
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/icons/)
 */
function Icon(props: IconProps) {
  const usaIconClass =
    typeof props.size === "number"
      ? `usa-icon usa-icon--size-${props.size}`
      : "usa-icon";
  const className = classnames(usaIconClass, props.className);

  return (
    <svg
      className={className}
      aria-hidden="true"
      focusable="false"
      role="img"
      fill={props.fill}
    >
      <use xlinkHref={`/img/sprite.svg#${props.name}`} />
    </svg>
  );
}

export default Icon;
