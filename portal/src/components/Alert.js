import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * An alert keeps users informed of important and sometimes time-sensitive changes.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/alert/)
 */
const Alert = React.forwardRef(
  ({ headingLevel = "2", role = "region", state = "error", ...props }, ref) => {
    const classes = classnames(
      `usa-alert usa-alert--${state}`,
      {
        "usa-alert--no-icon": props.noIcon,
        "usa-alert--slim": props.slim,
        "c-alert--neutral": props.neutral,
        "c-alert--auto-width": props.autoWidth,
      },
      props.className
    );

    return (
      <div className={classes} ref={ref} tabIndex="-1" role={role}>
        <div className="usa-alert__body">
          {props.heading && (
            <Heading
              level={headingLevel}
              className="usa-alert__heading"
              size={props.headingSize}
            >
              {props.heading}
            </Heading>
          )}
          <div className="usa-alert__text">{props.children}</div>
        </div>
      </div>
    );
  }
);

Alert.propTypes = {
  /** Additional classNames to add */
  className: PropTypes.string,
  /** Error message */
  children: PropTypes.node.isRequired,
  /** Sets the 'no-icon' style */
  noIcon: PropTypes.bool,
  /** Sets the 'slim' style */
  slim: PropTypes.bool,
  /** Optional heading */
  heading: PropTypes.node,
  /** HTML heading level */
  headingLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]),
  /**
   * Control the styling of the heading. By default, the `headingLevel` prop will be
   * used for styling, but styling and semantics don't always match up, so
   * you can override the styling by defining a `headingSize`.
   */
  headingSize: PropTypes.oneOf(["2", "3", "4", "5", "6"]),
  /** ARIA `role` */
  role: PropTypes.oneOf(["alert", "alertdialog", "region"]),
  /** Alert style */
  state: PropTypes.oneOf(["error", "info", "success", "warning"]),
  /** Adds custom style overriding the background color set by the state */
  neutral: PropTypes.bool,
  /** Adds custom style making the Alert only as wide as its contents require */
  autoWidth: PropTypes.bool,
};

// Explicitly set the display name, otherwise ForwardRef is used
Alert.displayName = "Alert";

export default Alert;
