import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

const Tag = ({ label, state }) => {
  // TODO (EMPLOYER-421) consider other states.
  const classes = classnames(
    "usa-tag",
    "text-bold",
    "padding-x-205",
    "padding-y-05",
    "radius-lg",
    {
      "text-success": state === "success",
      "bg-success-lighter": state === "success",
      "text-base-darker": state === "warning",
      "bg-warning-lighter": state === "warning",
    }
  );

  return <span className={classes}>{label}</span>;
};

Tag.propTypes = {
  label: PropTypes.string.isRequired,
  // TODO (EMPLOYER-421) consider other states.
  state: PropTypes.oneOf(["success", "warning"]).isRequired,
};

export default Tag;
