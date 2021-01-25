import Button from "../Button";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import { t } from "../../locales/i18n";

/**
 * Display form as a called-out amendment
 * in the Leave Admin claim review page.
 */

export const AmendmentForm = ({ className = "", onCancel, children }) => {
  const classes = classnames(
    `usa-alert usa-alert--info usa-alert--no-icon usa-form c-amendment-form`,
    className
  );

  return (
    <div className={classes}>
      <div className="usa-alert__body">
        <div className="usa-alert__text">{children}</div>
        <Button
          variation="unstyled"
          onClick={onCancel}
          className="margin-top-3"
        >
          {t("components.amendmentForm.cancel")}
        </Button>
      </div>
    </div>
  );
};

AmendmentForm.propTypes = {
  /** Additional classNames to add */
  className: PropTypes.string,
  /** Hides the amendment form */
  onCancel: PropTypes.func,
  children: PropTypes.node.isRequired,
};

export default AmendmentForm;
