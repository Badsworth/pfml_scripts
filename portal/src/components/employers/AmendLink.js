import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React from "react";
import { faEdit } from "@fortawesome/free-regular-svg-icons";
import { useTranslation } from "../../locales/i18n";

const AmendLink = () => {
  const { t } = useTranslation();

  return (
    <a href="" className="text-primary font-heading-xs text-normal">
      <FontAwesomeIcon icon={faEdit} className="fa-sm margin-right-0.5" />
      <span className="amend-text">
        {t("pages.employersClaimsReview.amend")}
      </span>
    </a>
  );
};

export default AmendLink;
