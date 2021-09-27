import EmployerClaim from "../../../models/EmployerClaim";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import formatDateRange from "../../../utils/formatDateRange";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

export const Confirmation = (props) => {
  const { t } = useTranslation();
  const {
    appLogic: {
      employers: { claim },
    },
    query: { absence_id },
  } = props;

  return (
    <React.Fragment>
      <Title>{t("pages.employersClaimsConfirmation.title")}</Title>
      <Trans
        i18nKey="pages.employersClaimsConfirmation.applicationIdLabel"
        values={{ absenceId: absence_id }}
      />
      <Trans
        i18nKey="pages.employersClaimsConfirmation.instructionsFollowUpDateLabel"
        values={{ date: formatDateRange(claim.follow_up_date) }}
        components={{
          div: <div />,
        }}
      />
      <Trans
        i18nKey="pages.employersClaimsConfirmation.instructions"
        components={{
          "contact-center-phone-link": (
            <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
          ),
          p: <p />,
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
      <p>
        {t(
          "pages.employersClaimsConfirmation.instructions_processingApplication"
        )}
      </p>
      <UserFeedback url={routes.external.massgov.feedbackEmployer} />
    </React.Fragment>
  );
};

Confirmation.propTypes = {
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      claim: PropTypes.instanceOf(EmployerClaim),
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withEmployerClaim(Confirmation);
