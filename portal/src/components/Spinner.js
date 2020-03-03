import PropTypes from "prop-types";
import React from "react";

/**
 * Animated icon used for indicating a progress/loading state
 */
export const Spinner = props => {
  return (
    <span
      className="c-spinner"
      aria-valuetext={props["aria-valuetext"]}
      role="progressbar"
    />
  );
};

Spinner.propTypes = {
  /** Text announced to screen readers */
  "aria-valuetext": PropTypes.string.isRequired
};

export default Spinner;
