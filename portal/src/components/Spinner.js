import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Animated icon used for indicating a progress/loading state
 */
export const Spinner = (props) => {
  const classes = classnames("c-spinner", {
    "height-3": props.small,
    "width-3": props.small,
  });

  return (
    <span
      className={classes}
      aria-valuetext={props["aria-valuetext"]}
      role="progressbar"
    />
  );
};

Spinner.propTypes = {
  /** Text announced to screen readers */
  "aria-valuetext": PropTypes.string.isRequired,
  /** Render small spinner */
  small: PropTypes.bool,
};

export default Spinner;
