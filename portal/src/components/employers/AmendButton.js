import Button from "../Button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import PropTypes from "prop-types";
import React from "react";
import { faEdit } from "@fortawesome/free-regular-svg-icons";
import { useTranslation } from "../../locales/i18n";

/**
 * Link with edit icon for amendable sections
 * in the Leave Admin claim review page.
 */

const AmendButton = ({ onClick }) => {
  const { t } = useTranslation();

  return (
    <span>
      <Button
        variation="unstyled"
        onClick={onClick}
        className="display-flex flex-align-end"
      >
        <FontAwesomeIcon icon={faEdit} className="margin-right-1" />
        <div className="amend-text">
          {t("pages.employersClaimsReview.amend")}
        </div>
      </Button>
    </span>
  );
};

AmendButton.propTypes = {
  /** Displays the amendment form */
  onClick: PropTypes.func,
};

export default AmendButton;
