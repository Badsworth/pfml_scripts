import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

const StepNumber = (props) => {
  const active = ["in_progress", "not_started"].includes(props.state);
  const completed = props.state === "completed";
  const filled = active || completed;

  const classes = [
    "radius-pill",
    "text-center",
    "height-3",
    "width-3",
    "tablet:height-5",
    "tablet:width-5",
    "font-sans-2xs",
    "tablet:font-sans-md",
  ];

  const outlineClasses = ["border-2px", "border-base", "text-base"];

  const filledClasses = ["text-base-lightest", "padding-top-2px"];

  const classNames = classnames(
    classes,
    filled ? filledClasses : outlineClasses,
    {
      "bg-black": completed,
      "bg-secondary": active,
    }
  );

  return (
    <div className={classNames}>
      <span className="usa-sr-only">{props.screenReaderPrefix}</span>{" "}
      {props.children}
    </div>
  );
};

StepNumber.propTypes = {
  /**
   * Label for the number announced to screen reader
   * e.g instead of announcing "1", provide a value "Step 1"
   */
  screenReaderPrefix: PropTypes.string.isRequired,
  /**
   * Style number as an outline. This takes precedent over any color
   */
  state: PropTypes.oneOf([
    "disabled",
    "completed",
    "in_progress",
    "not_started",
  ]),
  /**
   * Number to display. Currently only supports single digits.
   */
  children: PropTypes.oneOf([PropTypes.string, PropTypes.number]).isRequired,
};

export default StepNumber;
