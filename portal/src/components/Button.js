import PropTypes from "prop-types";
import React from "react";
import Spinner from "./Spinner";
import classnames from "classnames";

/**
 * Renders a `button` or `a` element styled as a Button component
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/button/)
 */
function Button({ type = "button", ...props }) {
  const showLoading = props.loading;
  // Maintain button width when in loading state by hiding content
  const children = showLoading ? (
    <React.Fragment>
      <span className="position-absolute width-full height-full left-0 top-1">
        <Spinner small aria-valuetext="loading" />
      </span>
      <span className="opacity-0">{props.children}</span>
    </React.Fragment>
  ) : (
    props.children
  );

  const classes = classnames(
    "usa-button position-relative",
    props.className,
    props.variation ? `usa-button--${props.variation}` : "",
    {
      "usa-button--inverse": props.inversed,
      "bg-white": props.variation === "outline",
      // This is weird, but we need this so that the inversed styling
      // kicks in when the variation is unstyled
      "usa-button--outline": props.inversed && props.variation === "unstyled",
      "minh-5 text-center": showLoading && props.variation === "unstyled",
    }
  );

  const button = (
    // Weird eslint thing where it throws an error since we're setting `type` via a variable:
    // eslint-disable-next-line react/button-has-type
    <button
      aria-controls={props["aria-controls"]}
      aria-expanded={props["aria-expanded"]}
      className={classes}
      name={props.name}
      onClick={props.onClick}
      type={type === "submit" ? "submit" : "button"}
      disabled={props.disabled || showLoading}
    >
      {children}
    </button>
  );

  const loadingMessageClasses = classnames(
    // full-width on small screens, beside button on larger screens
    "display-block",
    "mobile-lg:display-inline-block",
    // margin between button only on small screens
    "margin-top-1",
    "mobile-lg:margin-top-0",
    // center text to align with spinner on small screens
    "text-center",
    "mobile-lg:text-left"
  );

  const loadingMessage =
    showLoading && props.loadingMessage ? (
      <strong className={loadingMessageClasses}>{props.loadingMessage}</strong>
    ) : null;

  return (
    <React.Fragment>
      {button}
      {loadingMessage}
    </React.Fragment>
  );
}

Button.propTypes = {
  "aria-controls": PropTypes.string,
  "aria-expanded": PropTypes.oneOf(["true", "false"]),
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
   * Disable button and show loading indicator
   */
  loading: PropTypes.bool,
  /**
   * Display a loading message alongside the button
   */
  loadingMessage: PropTypes.string,
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
