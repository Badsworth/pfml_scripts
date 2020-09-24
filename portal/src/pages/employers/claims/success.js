import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import routes from "../../../../src/routes";
import { useTranslation } from "../../../locales/i18n";

export const Success = (props) => {
  const { t } = useTranslation();
  const { claim_id } = props.query;

  return (
    <React.Fragment>
      <Title>{t("pages.employersClaimsReview.success.header")}</Title>
      <Trans
        i18nKey="pages.employersClaimsReview.success.applicationIdLabel"
        components={{
          emphasized: <strong />,
        }}
        values={{ claimId: claim_id }}
      />
      <p>
        {t(
          "pages.employersClaimsReview.success.instructions_processingApplication"
        )}
      </p>
      <p>
        {t(
          "pages.employersClaimsReview.success.instructions_emailNotification"
        )}
      </p>
      <p>
        <Trans
          i18nKey="pages.employersClaimsReview.success.instructions_benefitsGuide"
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
    </React.Fragment>
  );
};

Success.propTypes = {
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default Success;
