import React from "react";
import classnames from "classnames";

interface StepNumberProps {
  /**
   * Label for the number announced to screen reader
   * e.g instead of announcing "1", provide a value "Step 1"
   */
  screenReaderPrefix: string;
  /**
   * Style number as an outline. This takes precedent over any color
   */
  state?:
    | "disabled"
    | "completed"
    | "in_progress"
    | "not_applicable"
    | "not_started";
  /**
   * Number to display. Currently only supports single digits.
   */
  children: string | number;
}

const StepNumber = (props: StepNumberProps) => {
  const active =
    props.state && ["in_progress", "not_started"].includes(props.state);
  const completed = props.state === "completed";
  const filled = active || completed;

  const classes = [
    "radius-pill",
    "text-center",
    "height-5",
    "width-5",
    "margin-top-2px", // align baseline of number with step title
    "font-sans-md",
  ];

  const outlineClasses = [
    "border-2px",
    // use line height to vertically center text
    "line-height-sans-5",
    "border-base",
    "text-base",
  ];

  const filledClasses = ["text-base-lightest", "line-height-sans-6"];

  const classNames = classnames(
    classes,
    filled ? filledClasses : outlineClasses,
    {
      "bg-black": completed,
      "bg-secondary": active,
    }
  );

  return (
    <div
      className={classNames}
      aria-label={`${props.screenReaderPrefix} ${props.children}`}
    >
      {props.children}
    </div>
  );
};

export default StepNumber;
