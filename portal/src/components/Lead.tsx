import React from "react";
import classnames from "classnames";

interface LeadProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Convenience component for rendering a page's "lead" (intro text) with the
 * expected USWDS utility classes for styling. Each Lead is a paragraph, so
 * you can use multiple of these if the lead text is more than one paragraph.
 */
const Lead = (props: LeadProps) => {
  const classes = classnames("usa-intro", props.className);

  return <p className={classes}>{props.children}</p>;
};

export default Lead;
