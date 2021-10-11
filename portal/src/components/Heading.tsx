import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Convenience component for rendering a page heading (h1-h6) with the
 * expected USWDS utility classes for styling. For a page title, use the
 * `Title` component instead.
 */
const Heading = (props) => {
  const { level, size, weight, id } = props;
  const HeadingElement = `h${level}`;
  const stylingLevel = size ? parseInt(size) : parseInt(level);

  const classes = classnames(props.className, {
    "font-heading-lg": stylingLevel === 1,
    "font-heading-md": stylingLevel === 2,
    "font-heading-sm": stylingLevel === 3,
    "font-heading-xs": stylingLevel === 4,
    "font-heading-2xs": stylingLevel >= 5,
    "text-bold": weight === "bold" || (!weight && stylingLevel < 5),
    "text-normal": weight === "normal" || (!weight && stylingLevel >= 5),
  });

  return (
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: any; id: any; className: string;... Remove this comment to see the full error message
    <HeadingElement id={id} className={classes}>
      {props.children}
    </HeadingElement>
  );
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
   * Target id for HTML heading element. Useful for targetting element for scrolled items.
   */
  id: PropTypes.string,
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
  /** Override the default heading font weight */
  weight: PropTypes.oneOf(["bold", "normal"]),
};

export default Heading;
