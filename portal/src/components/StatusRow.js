import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

const StatusRow = ({ className = "", children, label }) => {
  const classes = classnames(`margin-bottom-2 padding-bottom-2`, className);

  return (
    <div className={classes}>
      <Heading level="3" size="4" className="margin-bottom-1">
        {label}
      </Heading>
      {children}
    </div>
  );
};

StatusRow.propTypes = {
  /** Additional classNames to add */
  className: PropTypes.string,
  children: PropTypes.node.isRequired,
  label: PropTypes.node.isRequired,
};

export default StatusRow;
