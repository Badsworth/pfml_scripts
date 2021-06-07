import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import { uniqueId } from "lodash";

const Hint = (props) => {
  const hintClasses = classnames(
    `display-block line-height-sans-5 measure-5`,
    props.className,
    {
      // Use hint styling for small labels
      "usa-hint text-base-darkest": props.small,
      // Use lead styling for regular labels
      "usa-intro": !props.small,
    }
  );

  return (
    <span
      className={hintClasses}
      id={`${props.inputId || uniqueId("hint")}_hint`}
    >
      {props.children}
    </span>
  );
};

Hint.propTypes = {
  /**
   * Additional classes for hint
   */
  className: PropTypes.string,
  /**
   * Enable the smaller variant, which is used when the field is
   * already accompanied by larger question text (like a legend).
   * Defaults to false
   */
  small: PropTypes.bool,
  /**
   * For hints related to an input, the ID of the field this hint is for.
   */
  inputId: PropTypes.string,
  /**
   * Localized hint text
   */
  children: PropTypes.node.isRequired,
};

export default Hint;
