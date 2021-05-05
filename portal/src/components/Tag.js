import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

const Tag = ({ label, state }) => {
  const classes = classnames(
    "usa-tag",
    "display-inline-block",
    "text-bold",
    "padding-x-205",
    "padding-y-05",
    "radius-lg",
    "text-no-wrap",
    {
      "text-success": state === "success",
      "bg-success-lighter": state === "success",
      "text-base-darkest": state === "warning",
      "bg-warning-lighter": state === "warning",
      "text-error": state === "error",
      "bg-error-lighter": state === "error",
      "text-base-darker": state === "inactive",
      "bg-base-lightest": state === "inactive",
    }
  );

  return <span className={classes}>{label}</span>;
};

Tag.propTypes = {
  label: PropTypes.string.isRequired,
  state: PropTypes.oneOf(["success", "warning", "error", "inactive"])
    .isRequired,
};

export default Tag;
