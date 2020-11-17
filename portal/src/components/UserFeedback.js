import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import { useTranslation } from "../locales/i18n";

/**
 * Global user feedback module to gather data on user's experience with the site
 */
const UserFeedback = (props) => {
  const { t } = useTranslation();

  return (
    <div className="border-top-2px border-base-lighter margin-top-4 padding-top-4">
      <Heading level="2">{t("components.userFeedback.title")}</Heading>
      <p>{t("components.userFeedback.instructions")}</p>
      <p>
        <Trans
          i18nKey="components.userFeedback.surveyLink"
          components={{
            "user-feedback-link": (
              <a target="_blank" rel="noopener" href={props.url} />
            ),
          }}
        />
      </p>
    </div>
  );
};

UserFeedback.propTypes = {
  /** URL for the feedback survey */
  url: PropTypes.string.isRequired,
};

export default UserFeedback;
