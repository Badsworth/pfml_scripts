import React from "react";
import classnames from "classnames";

interface SpinnerProps {
  "aria-label": string;
  small?: boolean;
}

/**
 * Animated icon used for indicating a progress/loading state
 */
export const Spinner = (props: SpinnerProps) => {
  const classes = classnames("c-spinner", {
    "height-3": props.small,
    "width-3": props.small,
  });

  return (
    <span
      className={classes}
      aria-label={props["aria-label"]}
      role="progressbar"
    />
  );
};

export default Spinner;
