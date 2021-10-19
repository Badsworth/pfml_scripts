import { Trans, useTranslation } from "react-i18next";
import React from "react";

interface BetaBannerProps {
  feedbackUrl: string;
}

/**
 * Banner displayed at the top of the site to indicate the site is a work in progress,
 * and provide a method for sending feedback.
 */
const BetaBanner = (props: BetaBannerProps) => {
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

export default BetaBanner;
