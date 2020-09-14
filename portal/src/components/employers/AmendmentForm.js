import Button from "../Button";
import PropTypes from "prop-types";
import React from "react";
import { t } from "../../locales/i18n";

/**
 * Display form as a called-out amendment
 * in the Leave Admin claim review page.
 */

export const AmendmentForm = ({ onCancel, children }) => (
  <form
    className="usa-alert usa-alert--info usa-alert--no-icon c-amendment-form"
    tabIndex="-1"
  >
    <div className="usa-alert__body">
      <div className="usa-alert__text">{children}</div>
      <Button variation="unstyled" onClick={onCancel} className="margin-top-3">
        {t("components.amendmentForm.cancel")}
      </Button>
    </div>
  </form>
);

AmendmentForm.propTypes = {
  /** Hides the amendment form */
  onCancel: PropTypes.func,
  children: PropTypes.node.isRequired,
};

export default AmendmentForm;
