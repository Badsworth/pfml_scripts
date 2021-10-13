import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Thin wrapper around a fieldset element to normalize how
 * child margins are rendered
 */
const Fieldset = (props) => {
  // Add a top margin because the Legend's margin gets collapsed:
  // https://github.com/uswds/uswds/issues/4153
  const classNames = classnames("usa-fieldset margin-top-3", props.className);
  return <fieldset className={classNames}>{props.children}</fieldset>;
};

Fieldset.propTypes = {
  /**
   * Input components
   */
  children: PropTypes.node,
  /**
   * Additional CSS class names
   */
  className: PropTypes.string,
};

export default Fieldset;
