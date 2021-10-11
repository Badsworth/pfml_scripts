import React from "react";
import { useTranslation } from "../locales/i18n";

const NewTag = () => {
  const { t } = useTranslation();

  return (
    <strong className="usa-tag radius-md margin-left-1">
      {t("components.newTag")}
    </strong>
  );
};

export default NewTag;
