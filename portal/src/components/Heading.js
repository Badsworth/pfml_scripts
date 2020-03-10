import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Convenience component for rendering a page heading (h1-h6) with the
 * expected USWDS utility classes for styling. For a page title, use the
 * `Title` component instead.
 */
const Heading = props => {
  const HeadingElement = `h${props.level}`;
  const stylingLevel = props.size ? props.size : props.level;

  const classes = classnames(props.className, {
    "font-heading-xl text-bold": stylingLevel === "1",
    "font-heading-lg text-bold": stylingLevel === "2",
    "font-heading-md text-bold": stylingLevel === "3",
    "font-heading-sm text-bold": stylingLevel === "4",
    "font-heading-xs text-normal": stylingLevel === "5",
    "font-heading-2xs text-normal": stylingLevel === "6",
  });

  return <HeadingElement className={classes}>{props.children}</HeadingElement>;
};

Heading.propTypes = {
  /**
   * Heading text
   */
  children: PropTypes.node.isRequired,
  /**
   * Additional classes to apply to the HTML heading element. Useful for adding
   * utility classes to control spacing.
   */
  className: PropTypes.string,
  /**
   * HTML heading level. It's important to not skip one or more heading levels.
   * To override the styling, use the `size` prop. To render an `h1`, use the
   * `<Title>` component instead.
   */
  level: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
  /**
   * Control the styling of the heading. By default, the `level` prop will be
   * used for styling, but styling and semantics don't always match up, so
   * you can override the styling by defining a `size`.
   */
  size: PropTypes.oneOf(["1", "2", "3", "4", "5", "6"]),
};

export default Heading;
