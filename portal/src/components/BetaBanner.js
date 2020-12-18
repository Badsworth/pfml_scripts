import { Trans, useTranslation } from "react-i18next";
import PropTypes from "prop-types";
import React from "react";

/**
 * Banner displayed at the top of the site to indicate the site is a work in progress,
 * and provide a method for sending feedback.
 */
const BetaBanner = (props) => {
  const { t } = useTranslation();

  return (
    <div className="bg-base-lightest">
      <div className="c-beta-banner">
        <span className="display-inline-block bg-secondary margin-right-1 padding-x-2 text-bold text-white">
          {t("components.betaBanner.tag")}
        </span>
        <Trans
          i18nKey="components.betaBanner.message"
          components={{
            "user-feedback-link": (
              <a target="_blank" rel="noopener" href={props.feedbackUrl} />
            ),
          }}
        />
      </div>
    </div>
  );
};

BetaBanner.propTypes = {
  /** URL for the survey */
  feedbackUrl: PropTypes.string.isRequired,
};

export default BetaBanner;
