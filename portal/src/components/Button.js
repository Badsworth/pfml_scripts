import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Renders a `button` or `a` element styled as a Button component
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/button/)
 */
function Button({ type = "button", ...props }) {
  const classes = classnames(
    "usa-button",
    props.className,
    props.variation ? `usa-button--${props.variation}` : "",
    {
      "usa-button--inverse": props.inversed,
      // This is weird, but we need this so that the inversed styling
      // kicks in when the variation is unstyled
      "usa-button--outline": props.inversed && props.variation === "unstyled",
    }
  );

  return (
    // Weird eslint thing where it throws an error since we're setting `type` via a variable:
    // eslint-disable-next-line react/button-has-type
    <button
      className={classes}
      name={props.name}
      onClick={props.onClick}
      type={type}
      disabled={props.disabled}
    >
      {props.children}
    </button>
  );
}

Button.propTypes = {
  /**
   * Button text
   */
  children: PropTypes.node.isRequired,
  /**
   * Additional classes to apply to the HTML element. Useful for adding
   * utility classes to control spacing.
   */
  className: PropTypes.string,
  /**
   * Apply the "inverse" style modifier
   */
  inversed: PropTypes.bool,
  /**
   * HTML `name` attribute
   */
  name: PropTypes.string,
  /**
   * HTML `onClick` attribute
   */
  onClick: PropTypes.func,
  /**
   * HTML `type` attribute
   */
  type: PropTypes.oneOf(["button", "submit"]),
  /**
   * Disable button click
   */
  disabled: PropTypes.bool,
  /**
   * Change the default button style
   */
  variation: PropTypes.oneOf([
    "accent-cool",
    "outline",
    "secondary",
    "unstyled",
  ]),
};

export default Button;
