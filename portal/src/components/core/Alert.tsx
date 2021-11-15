import Heading from "./Heading";
import React from "react";
import classnames from "classnames";
import isBlank from "../../utils/isBlank";

interface AlertProps {
  className?: string;
  children: React.ReactNode;
  noIcon?: boolean;
  slim?: boolean;
  heading?: React.ReactNode;
  headingLevel?: "2" | "3" | "4" | "5" | "6";
  /**
   * Control the styling of the heading. By default, the `headingLevel` prop will be
   * used for styling, but styling and semantics don't always match up, so
   * you can override the styling by defining a `headingSize`.
   */
  headingSize?: "2" | "3" | "4" | "5" | "6";
  role?: "alert" | "alertdialog" | "region";
  state?: "error" | "info" | "success" | "warning";
  neutral?: boolean;
  autoWidth?: boolean;
}

/**
 * An alert keeps users informed of important and sometimes time-sensitive changes.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/alert/)
 */
const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      headingLevel = "2",
      role = "region",
      state = "error",
      ...props
    }: AlertProps,
    ref
  ) => {
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
      <div className={classes} role={role} ref={ref} tabIndex={-1}>
        <div className="usa-alert__body">
          {!isBlank(props.heading) && (
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

// Explicitly set the display name, otherwise ForwardRef is used
Alert.displayName = "Alert";

export default Alert;
