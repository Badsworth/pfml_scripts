import { Trans, useTranslation } from "react-i18next";
import Alert from "../Alert";
import PropTypes from "prop-types";
import React from "react";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../../src/routes";

/**
 * Banner that announces upcoming features and comms in Employer Portal
 */
export const NewsBanner = ({ className }) => {
  const { t } = useTranslation();
  const shouldShowDashboard = isFeatureEnabled("employerShowDashboard");

  return (
    <Alert
      className={className}
      state="info"
      heading={t("components.newsBanner.header")}
    >
      <p>
        <Trans
          i18nKey="components.newsBanner.body"
          tOptions={{ context: shouldShowDashboard && "live" }}
          components={{
            "learn-more-link": (
              <a
                href={routes.external.massgov.employerDashboard}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
    </Alert>
  );
};

NewsBanner.propTypes = {
  className: PropTypes.string,
};
