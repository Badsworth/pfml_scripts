import Heading from "./Heading";
import React from "react";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Global user feedback module to gather data on user's experience with the site
 */
const UserFeedback = () => {
  const { t } = useTranslation();

  return (
    <div className="border-top-2px border-base-lighter margin-top-2 padding-top-2">
      <Heading level="2">{t("components.userFeedback.title")}</Heading>
      <p>{t("components.userFeedback.instructions")}</p>
      <p>
        <Trans
          i18nKey="components.userFeedback.surveyLink"
          components={{
            "user-feedback-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.userFeedback}
              />
            ),
          }}
        />
      </p>
    </div>
  );
};

export default UserFeedback;
