import withUser, { WithUserProps } from "../../../hoc/withUser";
import BackButton from "../../../components/BackButton";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Success = (
  props: WithUserProps & { query: { absence_id?: string } }
) => {
  const { t } = useTranslation();
  const {
    appLogic,
    query: { absence_id },
  } = props;

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.employersClaimsSuccess.backToDashboardLabel")}
        href={appLogic.portalFlow.getNextPageRoute("BACK")}
      />
      <Title>{t("pages.employersClaimsSuccess.title")}</Title>
      <Trans
        i18nKey="pages.employersClaimsSuccess.applicationIdLabel"
        values={{ absenceId: absence_id }}
      />
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

export default withUser(Success);