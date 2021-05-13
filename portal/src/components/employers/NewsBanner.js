import { Trans, useTranslation } from "react-i18next";
import Alert from "../Alert";
import PropTypes from "prop-types";
import React from "react";

/**
 * Banner that announces upcoming features and comms in Employer Portal
 */
export const NewsBanner = ({ className }) => {
  const { t } = useTranslation();

  return (
    <Alert
      className={className}
      state="info"
      heading={t("components.newsBanner.header")}
    >
      <p>
        <Trans
          i18nKey="components.newsBanner.body"
          // TODO (EMPLOYER-1296): Add Mass.gov link to banner
          // components={{
          //   "learn-more-link": (
          //     <a
          //       href={routes.external.massgov.employerDashboard}
          //       target="_blank"
          //       rel="noopener"
          //     />
          //   ),
          // }}
        />
      </p>
    </Alert>
  );
};

NewsBanner.propTypes = {
  className: PropTypes.string,
};
