import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Convenience component for rendering a page's title with the
 * expected USWDS utility classes for styling. There should only
 * be one of these per page!
 */
const Title = ({ component = "h1", ...props }) => {
  const TitleElement = component;
  const classes = classnames(
    "font-heading-xl line-height-sans-2 margin-top-0 margin-bottom-2",
    {
      "usa-legend": component === "legend",
    }
  );

  return <TitleElement className={classes}>{props.children}</TitleElement>;
};

Title.propTypes = {
  /**
   * Title text
   */
  children: PropTypes.node.isRequired,
  /**
   * HTML element used to render the page title
   */
  component: PropTypes.oneOf(["h1", "legend"]),
};

export default Title;
