import withEmployerClaim, {
  WithEmployerClaimProps,
} from "../../../hoc/withEmployerClaim";
import BackButton from "../../../components/BackButton";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import formatDate from "../../../utils/formatDate";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Success = (props: WithEmployerClaimProps) => {
  const { t } = useTranslation();
  const {
    appLogic,
    claim: { fullName, fineos_absence_id, lastReviewedAt },
  } = props;

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.employersClaimsSuccess.backToDashboardLabel")}
        href={appLogic.portalFlow.getNextPageRoute("BACK")}
      />
      <Title>{t("pages.employersClaimsSuccess.title")}</Title>
      <p>
        <Trans
          i18nKey="pages.employersClaimsSuccess.employeeNameLabel"
          values={{ employeeName: fullName }}
        />
      </p>
      <p>
        <Trans
          i18nKey="pages.employersClaimsSuccess.applicationIdLabel"
          values={{ absenceId: fineos_absence_id }}
        />
      </p>
      <p>
        <Trans
          i18nKey="pages.employersClaimsSuccess.reviewedOnLabel"
          values={{ date: formatDate(lastReviewedAt).short() }}
        />
      </p>
      <p>
        {t("pages.employersClaimsSuccess.instructions_processingApplication")}
      </p>
      <p>
        <Trans
          i18nKey="pages.employersClaimsSuccess.instructions_reimbursement"
          components={{
            "reimbursements-link": (
              <a
                href={routes.external.massgov.employerReimbursements}
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
          }}
        />
      </p>
      <UserFeedback url={routes.external.massgov.feedbackEmployer} />
    </React.Fragment>
  );
};

export default withEmployerClaim(Success);
