import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Link styled as button.
 */
const ButtonLink = (props) => {
  const classes = classnames(
    "usa-button",
    props.variation ? `usa-button--${props.variation}` : ""
  );

  return (
    <Link href={props.href}>
      <a className={classes}>{props.children}</a>
    </Link>
  );
};

ButtonLink.propTypes = {
  /**
   * Button text.
   */
  children: PropTypes.node.isRequired,
  /**
   * Href for link.
   */
  href: PropTypes.string.isRequired,
  /**
   * If present, determines button style variation.
   */
  variation: PropTypes.oneOf(["outline", "secondary", "accent-cool"]),
};

export default ButtonLink;
