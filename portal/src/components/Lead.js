import PropTypes from "prop-types";
import React from "react";

/**
 * Convenience component for rendering a page's "lead" (intro text) with the
 * expected USWDS utility classes for styling. Each Lead is a paragraph, so
 * you can use multiple of these if the lead text is more than one paragraph.
 */
const Lead = props => {
  return <p className="usa-intro">{props.children}</p>;
};

Lead.propTypes = {
  /**
   * Lead text
   */
  children: PropTypes.node.isRequired,
};

export default Lead;
