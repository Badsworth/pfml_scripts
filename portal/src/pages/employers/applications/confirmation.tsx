import withEmployerClaim, {
  WithEmployerClaimProps,
} from "../../../hoc/withEmployerClaim";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import { getSoonestReviewableFollowUpDate } from "../../../models/ManagedRequirement";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Confirmation = (props: WithEmployerClaimProps) => {
  const { t } = useTranslation();
  const { claim } = props;

  return (
    <React.Fragment>
      <Title>{t("pages.employersClaimsConfirmation.title")}</Title>
      <Trans
        i18nKey="pages.employersClaimsConfirmation.applicationIdLabel"
        values={{ absenceId: claim.fineos_absence_id }}
      />
      <Trans
        i18nKey="pages.employersClaimsConfirmation.instructionsFollowUpDateLabel"
        values={{
          date: getSoonestReviewableFollowUpDate(claim.managed_requirements),
        }}
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
