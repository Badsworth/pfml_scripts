import PropTypes from "prop-types";
import React from "react";

/**
 * Line of smaller text that can be nested within a Heading. Visually,
 * this text appears as a label above the heading, but to screen readers
 * it reads as part of the heading. This is useful for avoiding unnecessary
 * heading levels.
 */
function HeadingPrefix(props) {
  return (
    <span className="display-block font-heading-2xs margin-bottom-2 text-base-dark text-bold">
      {props.children}
    </span>
  );
}

HeadingPrefix.propTypes = {
  children: PropTypes.node.isRequired,
};

export default HeadingPrefix;
