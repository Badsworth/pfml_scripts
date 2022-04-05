import LeaveSpansBenefitYearsMessage from "src/components/LeaveSpansBenefitYearsMessage";
import QuestionPage from "./QuestionPage";
import React from "react";
import { WithBenefitsApplicationProps } from "../hoc/withBenefitsApplication";
import { useTranslation } from "src/locales/i18n";

export const LeaveSpansBenefitYearInterstitial = (
  props: WithBenefitsApplicationProps
) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const handleSave = async () => {
    return await appLogic.portalFlow.goToNextPage(
      { claim },
      { claim_id: claim.application_id }
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsLeaveSpansBenefitYears.title")}
      onSave={handleSave}
      continueButtonLabel={t(
        "pages.claimsLeaveSpansBenefitYears.continueLabel"
      )}
    >
      <h2>{t("shared.claimsLeaveSpansBenefitYears.title")}</h2>
      <LeaveSpansBenefitYearsMessage claim={claim} />
    </QuestionPage>
  );
};

export default LeaveSpansBenefitYearInterstitial;
