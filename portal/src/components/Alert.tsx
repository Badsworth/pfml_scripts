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
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'headingLevel' does not exist on type '{ ... Remove this comment to see the full error message
  ({ headingLevel = "2", role = "region", state = "error", ...props }, ref) => {
    const classes = classnames(
      `usa-alert usa-alert--${state}`,
      {
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'noIcon' does not exist on type '{ childr... Remove this comment to see the full error message
        "usa-alert--no-icon": props.noIcon,
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'slim' does not exist on type '{ children... Remove this comment to see the full error message
        "usa-alert--slim": props.slim,
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'neutral' does not exist on type '{ child... Remove this comment to see the full error message
        "c-alert--neutral": props.neutral,
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'autoWidth' does not exist on type '{ chi... Remove this comment to see the full error message
        "c-alert--auto-width": props.autoWidth,
      },
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'className' does not exist on type '{ chi... Remove this comment to see the full error message
      props.className
    );

    return (
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'ForwardedRef<unknown>' is not assignable to ... Remove this comment to see the full error message
      <div className={classes} role={role} ref={ref} tabIndex="-1">
        <div className="usa-alert__body">
          {/* @ts-expect-error ts-migrate(2339) FIXME: Property 'heading' does not exist on type '{ child... Remove this comment to see the full error message */}
          {props.heading && (
            <Heading
              level={headingLevel}
              className="usa-alert__heading"
              // @ts-expect-error ts-migrate(2339) FIXME: Property 'headingSize' does not exist on type '{ c... Remove this comment to see the full error message
              size={props.headingSize}
            >
              {/* @ts-expect-error ts-migrate(2339) FIXME: Property 'heading' does not exist on type '{ child... Remove this comment to see the full error message */}
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
  // @ts-expect-error ts-migrate(2322) FIXME: Type '{ className: PropTypes.Requireable<string>; ... Remove this comment to see the full error message
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
