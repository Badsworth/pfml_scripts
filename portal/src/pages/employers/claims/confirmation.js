import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import formatDateRange from "../../../utils/formatDateRange";
import routes from "../../../../src/routes";
import { useTranslation } from "../../../locales/i18n";

export const Confirmation = (props) => {
  const { t } = useTranslation();
  // TODO (EMPLOYER-363) - utilize withEmployerClaim HOC when due_date is available in Claim model
  const { absence_id, due_date } = props.query;

  return (
    <React.Fragment>
      <Title>{t("pages.employersClaimsConfirmation.title")}</Title>
      <Trans
        i18nKey="pages.employersClaimsConfirmation.applicationIdLabel"
        values={{ absenceId: absence_id }}
      />
      <Trans
        i18nKey="pages.employersClaimsConfirmation.reviewByLabel"
        values={{ employerDueDate: formatDateRange(due_date) }}
        components={{
          div: <div />,
        }}
      />
      <Trans
        i18nKey="pages.employersClaimsConfirmation.instructions"
        components={{
          p: <p />,
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
      <p>
        <Trans
          i18nKey="pages.employersClaimsConfirmation.instructions_benefitsGuide"
          components={{
            "benefits-guide-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.benefitsGuide}
              />
            ),
          }}
        />
      </p>
      <UserFeedback />
    </React.Fragment>
  );
};

Confirmation.propTypes = {
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
    due_date: PropTypes.string.isRequired,
  }).isRequired,
};

export default Confirmation;
