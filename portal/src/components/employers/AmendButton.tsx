import Button from "../Button";
import Icon from "../Icon";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../../locales/i18n";

/**
 * Link with edit icon for amendable sections
 * in the Leave Admin claim review page.
 */

const AmendButton = ({ onClick }) => {
  const { t } = useTranslation();

  return (
    <span className="c-amend-button">
      <Button variation="unstyled" onClick={onClick} data-test="amend-button">
        <Icon
          name="edit"
          className="text-middle margin-right-05 margin-top-neg-05"
        />
        <span className="amend-text">{t("components.amendButton.amend")}</span>
      </Button>
    </span>
  );
};

AmendButton.propTypes = {
  /** Displays the amendment form */
  onClick: PropTypes.func,
};

export default AmendButton;
