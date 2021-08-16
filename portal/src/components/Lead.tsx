import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Convenience component for rendering a page's "lead" (intro text) with the
 * expected USWDS utility classes for styling. Each Lead is a paragraph, so
 * you can use multiple of these if the lead text is more than one paragraph.
 */
const Lead = (props) => {
  const classes = classnames("usa-intro", props.className);

  return <p className={classes}>{props.children}</p>;
};

Lead.propTypes = {
  /**
   * Lead text
   */
  children: PropTypes.node.isRequired,
  /**
   * Additional classes to include on the <p> tag
   */
  className: PropTypes.string,
};

export default Lead;
