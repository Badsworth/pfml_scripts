import { Trans, useTranslation } from "react-i18next";
import Alert from "../Alert";
import PropTypes from "prop-types";
import React from "react";
import routes from "../../routes";

/**
 * Banner that tells the user that they will soon need to verify their
 * accounts.
 */
export const AccountVerificationBanner = ({ className }) => {
  const { t } = useTranslation();

  return (
    <Alert
      className={className}
      state="info"
      heading={t("components.accountVerificationBanner.header")}
    >
      <p>
        <Trans
          i18nKey="components.accountVerificationBanner.body"
          components={{
            "learn-more-link": (
              <a
                href={routes.external.massgov.employerAccount}
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

AccountVerificationBanner.propTypes = {
  className: PropTypes.string,
};
