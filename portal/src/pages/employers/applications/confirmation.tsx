import { AppLogic } from "../../../hooks/useAppLogic";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import formatDateRange from "../../../utils/formatDateRange";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

interface ConfirmationProps {
  appLogic: AppLogic;
  query: {
    absence_id: string;
  };
}

export const Confirmation = (props: ConfirmationProps) => {
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

export default withEmployerClaim(Confirmation);
