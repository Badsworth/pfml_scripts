import React from "react";
import classnames from "classnames";

export interface TagProps {
  className?: string;
  label: string;
  /**
   * Keywords for sharing common styling for similar Tag states. The state value
   * may not exactly match the tag content (i.e "Approved" is a success-like state).
   */
  state?: "success" | "warning" | "error" | "inactive";
}

/**
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/tag/)
 */
const Tag = ({ label, state, className }: TagProps) => {
  const classes = classnames(
    "usa-tag",
    "display-inline-block",
    "text-bold",
    "text-middle",
    "text-center",
    "text-no-wrap",
    {
      "text-success-dark": state === "success",
      "bg-success-lighter": state === "success",
      "text-base-darkest": state === "warning",
      "bg-warning-lighter": state === "warning",
      "text-error-darker": state === "error",
      "bg-error-lighter": state === "error",
      "text-base-darker": state === "inactive",
      "bg-base-lightest": state === "inactive",
    },
    className
  );

  return <span className={classes}>{label}</span>;
};

export default Tag;
