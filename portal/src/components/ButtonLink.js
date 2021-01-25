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
    {
      "usa-button--inverse": props.inversed,
      // This is weird, but we need this so that the inversed styling
      // kicks in when the variation is unstyled
      "usa-button--outline": props.inversed && props.variation === "unstyled",
    },
    { disabled: props.disabled }
  );

  if (props.disabled) {
    return (
      <button
        type="button"
        className={classes}
        aria-label={props.ariaLabel}
        disabled
      >
        {props.children}
      </button>
    );
  }

  return (
    <Link href={props.href}>
      <a className={classes} aria-label={props.ariaLabel}>
        {props.children}
      </a>
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
   * Button's aria-label text.
   */
  ariaLabel: PropTypes.string,
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
  /**
   * Apply the "inverse" style modifier
   */
  inversed: PropTypes.bool,
};

export default ButtonLink;
