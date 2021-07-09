import Button from "../Button";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * Display form as a called-out amendment
 * in the Leave Admin claim review page.
 */

export const AmendmentForm = ({
  className = "",
  onDestroy,
  children,
  destroyButtonLabel,
}) => {
  const classes = classnames(
    `usa-alert usa-alert--info usa-alert--no-icon usa-form c-amendment-form border-y border-y-width-1px border-right border-right-width-1px`,
    className
  );

  return (
    <div className={classes}>
      <div className="usa-alert__body">
        <div className="usa-alert__text">{children}</div>
        <div className="border-top border-width-1px margin-top-4 margin-bottom-1 border-base-light">
          <Button
            data-test="amendment-destroy-button"
            variation="unstyled"
            className="margin-top-3 text-red"
            onClick={onDestroy}
          >
            {destroyButtonLabel}
          </Button>
        </div>
      </div>
    </div>
  );
};

AmendmentForm.propTypes = {
  /** Additional classNames to add */
  className: PropTypes.string,
  /** Hides the amendment form */
  onDestroy: PropTypes.func.isRequired,
  children: PropTypes.node.isRequired,
  destroyButtonLabel: PropTypes.string.isRequired,
};

export default AmendmentForm;
