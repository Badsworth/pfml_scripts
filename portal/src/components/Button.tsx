import React from "react";
import Spinner from "./Spinner";
import classnames from "classnames";

interface ButtonProps {
  "aria-controls"?: string;
  "aria-expanded"?: "true" | "false";
  "aria-label"?: string;
  children: React.ReactNode;
  className?: string;
  loading?: boolean;
  loadingMessage?: string;
  inversed?: boolean;
  name?: string;
  onClick?: (...args: any[]) => any;
  type?: "button" | "submit";
  disabled?: boolean;
  variation?: "accent-cool" | "outline" | "secondary" | "unstyled";
}

/**
 * Renders a `button` element styled as a Button component
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/button/)
 */
function Button({ type = "button", ...props }: ButtonProps) {
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
      aria-label={props["aria-label"]}
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

export default Button;
