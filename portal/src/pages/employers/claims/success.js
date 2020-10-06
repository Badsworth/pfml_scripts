import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import routes from "../../../../src/routes";
import { useTranslation } from "../../../locales/i18n";

export const Success = (props) => {
  const { t } = useTranslation();
  const { absence_id } = props.query;

  return (
    <React.Fragment>
      <Title>{t("pages.employersClaimsSuccess.title")}</Title>
      <Trans
        i18nKey="pages.employersClaimsSuccess.applicationIdLabel"
        values={{ absenceId: absence_id }}
      />
      <p>
        {t("pages.employersClaimsSuccess.instructions_processingApplication")}
      </p>
      <p>{t("pages.employersClaimsSuccess.instructions_emailNotification")}</p>
      <p>
        <Trans
          i18nKey="pages.employersClaimsSuccess.instructions_benefitsGuide"
          components={{
            "benefits-guide-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.pfmlBenefitsGuide}
              />
            ),
          }}
        />
      </p>
      <UserFeedback />
    </React.Fragment>
  );
};

Success.propTypes = {
  query: PropTypes.shape({
    absence_id: PropTypes.string,
  }),
};

export default Success;
