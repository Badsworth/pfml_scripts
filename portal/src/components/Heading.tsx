import React from "react";
import classnames from "classnames";

interface HeadingProps {
  /**
   * Heading text
   */
  children: React.ReactNode;
  /**
   * Additional classes to apply to the HTML heading element. Useful for adding
   * utility classes to control spacing.
   */
  className?: string;
  /**
   * Target id for HTML heading element. Useful for targetting element for scrolled items.
   */
  id?: string;
  /**
   * HTML heading level. It's important to not skip one or more heading levels.
   * To override the styling, use the `size` prop. To render an `h1`, use the
   * `<Title>` component instead.
   */
  level: "2" | "3" | "4" | "5" | "6";
  /**
   * Control the styling of the heading. By default, the `level` prop will be
   * used for styling, but styling and semantics don't always match up, so
   * you can override the styling by defining a `size`.
   */
  size?: "1" | "2" | "3" | "4" | "5" | "6";
  /** Override the default heading font weight */
  weight?: "bold" | "normal";
}

/**
 * Convenience component for rendering a page heading (h1-h6) with the
 * expected USWDS utility classes for styling. For a page title, use the
 * `Title` component instead.
 */
const Heading = (props: HeadingProps) => {
  const { children, level, size, weight, id } = props;
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

  const headingProps = { id, className: classes, children };

  /* eslint-disable jsx-a11y/heading-has-content */
  switch (level) {
    case "2":
      return <h2 {...headingProps} />;
    case "3":
      return <h3 {...headingProps} />;
    case "4":
      return <h4 {...headingProps} />;
    case "5":
      return <h5 {...headingProps} />;
    case "6":
      return <h6 {...headingProps} />;
  }
};

export default Heading;
