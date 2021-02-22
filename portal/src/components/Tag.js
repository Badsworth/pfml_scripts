import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

const Tag = ({ label, state }) => {
  // TODO (EMPLOYER-421) consider other states.
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
    }
  );

  return <span className={classes}>{label}</span>;
};

Tag.propTypes = {
  label: PropTypes.string.isRequired,
  // TODO (EMPLOYER-421) consider other states.
  state: PropTypes.oneOf(["success", "warning", "error"]).isRequired,
};

export default Tag;
