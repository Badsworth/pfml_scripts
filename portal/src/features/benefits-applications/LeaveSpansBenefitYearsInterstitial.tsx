import BackButton from "src/components/BackButton";
import ButtonLink from "src/components/ButtonLink";
import LeaveSpansBenefitYearsMessage from "src/features/benefits-applications/LeaveSpansBenefitYearsMessage";
import React from "react";
import Spinner from "src/components/core/Spinner";
import Title from "src/components/core/Title";
import { WithBenefitsApplicationProps } from "../../hoc/withBenefitsApplication";
import routes from "src/routes";
import { useTranslation } from "src/locales/i18n";

export const LeaveSpansBenefitYearInterstitial = (
  props: WithBenefitsApplicationProps
) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  if (
    claim.computed_application_split === null ||
    claim.computed_earliest_submission_date === null
  ) {
    appLogic.portalFlow.goTo(routes.applications.index, {}, { redirect: true });

    return (
      <div className="margin-top-8 text-center">
        <Spinner
          aria-label={t("pages.claimsLeaveSpansBenefitYears.loadingLabel")}
        />
      </div>
    );
  }

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.claimsLeaveSpansBenefitYears.title")}</Title>
      <LeaveSpansBenefitYearsMessage
        computed_application_split={claim.computed_application_split}
        computed_earliest_submission_date={
          claim.computed_earliest_submission_date
        }
      />
      <ButtonLink
        className="text-no-underline text-white"
        href={appLogic.portalFlow.getNextPageRoute(
          "CONTINUE",
          {},
          { claim_id: claim.application_id }
        )}
      >
        {t("pages.claimsLeaveSpansBenefitYears.continueLabel")}
      </ButtonLink>
    </React.Fragment>
  );
};

export default LeaveSpansBenefitYearInterstitial;
