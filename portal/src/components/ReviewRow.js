import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import useUniqueId from "../hooks/useUniqueId";

/**
 * The ReviewRow component encapsulates a single reviewable row of form data.
 */
const ReviewRow = (props) => {
  const id = useUniqueId("descriptionLabel");
  const classes = classnames("margin-bottom-2 padding-bottom-2", {
    "border-bottom-2px border-base-lighter": !props.noBorder,
  });

  return (
    <div className={classes}>
      <dt id={id}>
        <Heading level={props.level} size="4" className="margin-bottom-1">
          {props.label}
        </Heading>
      </dt>
      <dd className="margin-0" aria-labelledby={id}>
        {props.children}
      </dd>
    </div>
  );
};

ReviewRow.defaultProps = {
  level: "4",
};

ReviewRow.propTypes = {
  /**
   * The content you want the user to review
   */
  children: PropTypes.node.isRequired,
  /**
   * Label describing the content to be reviewed.
   */
  label: PropTypes.string.isRequired,
  /**
   * The heading level to use for the label
   */
  level: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
  /** Exclude the bottom border. Useful if a child already includes a border. */
  noBorder: PropTypes.bool,
};

export default ReviewRow;
