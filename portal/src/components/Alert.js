import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";

/**
 * An alert keeps users informed of important and sometimes time-sensitive changes.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/alert/)
 */
const Alert = React.forwardRef(
  ({ role = "region", state = "error", ...props }, ref) => {
    return (
      <div className={`usa-alert usa-alert--${state}`} ref={ref} tabIndex="-1">
        <div className="usa-alert__body" role={role}>
          {props.heading && (
            <Heading level="2" className="usa-alert__heading">
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
  /** Error message */
  children: PropTypes.node.isRequired,
  /** Optional heading */
  heading: PropTypes.node,
  /** ARIA `role` */
  role: PropTypes.oneOf(["alert", "alertdialog", "region"]),
  /** Alert style */
  state: PropTypes.oneOf(["error", "info", "success", "warning"]),
};

// Explicitly set the display name, otherwise ForwardRef is used
Alert.displayName = "Alert";

export default Alert;
