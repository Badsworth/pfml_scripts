import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Next.js [`Link`](https://nextjs.org/docs/api-reference/next/link)
 * styled as a button. Provides client-side transitions between routes.
 */
const ButtonLink = (props) => {
  const classes = classnames(
    "usa-button",
    props.className,
    props.variation ? `usa-button--${props.variation}` : "",
    { disabled: props.disabled }
  );

  if (props.disabled) {
    return (
      <button className={classes} type="button" disabled>
        {props.children}
      </button>
    );
  }

  return (
    <Link href={props.href}>
      <a className={classes}>{props.children}</a>
    </Link>
  );
};

ButtonLink.propTypes = {
  /**
   * Disable button click
   */
  disabled: PropTypes.bool,
  /**
   * Button text.
   */
  children: PropTypes.node.isRequired,
  /**
   * Additional classes to apply to the HTML element. Useful for adding
   * utility classes to control spacing.
   */
  className: PropTypes.string,
  /**
   * Href for link.
   */
  href: PropTypes.string.isRequired,
  /**
   * If present, determines button style variation.
   */
  variation: PropTypes.oneOf([
    "outline",
    "secondary",
    "accent-cool",
    "unstyled",
  ]),
};

export default ButtonLink;
