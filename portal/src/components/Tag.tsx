import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

const Tag = ({ label, state, className }) => {
  const classes = classnames(
    "usa-tag",
    "display-inline-block",
    "text-bold",
    "padding-y-05",
    "radius-lg",
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
      "bg-primary-lighter": state === "pending",
      "text-primary": state === "pending",
      "padding-x-205": !className,
    },
    className
  );

  return <span className={classes}>{label}</span>;
};

Tag.propTypes = {
  className: PropTypes.string,
  label: PropTypes.string.isRequired,
  state: PropTypes.oneOf(["success", "warning", "error", "inactive", "pending"])
    .isRequired,
};

export default Tag;
