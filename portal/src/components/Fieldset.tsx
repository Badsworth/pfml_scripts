import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Thin wrapper around a fieldset element to normalize how
 * child margins are rendered
 */
const Fieldset = (props) => {
  const classNames = classnames("usa-fieldset", props.className);
  return (
    <fieldset className={classNames}>
      <span>{props.children}</span>
    </fieldset>
  );
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
