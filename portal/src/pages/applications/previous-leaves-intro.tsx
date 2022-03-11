import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Details from "../../components/core/Details";
import Heading from "../../components/core/Heading";
import Icon from "../../components/core/Icon";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import { useTranslation } from "../../locales/i18n";

export const PreviousLeavesIntro = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const startDate = formatDate(claim.leaveStartDate).full();
  const otherLeaveStartDate = formatDate(
    claim.computed_start_dates.other_reason
  ).full();

  const handleSave = async () => {
    return await appLogic.portalFlow.goToNextPage(
      { claim },
      { claim_id: claim.application_id }
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesIntro.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsPreviousLeavesIntro.sectionLabel")}
      </Heading>

      <Heading level="3">
        <Icon
          name="check"
          size={3}
          className="text-secondary text-middle margin-right-1 margin-top-neg-05"
        />
        <Trans
          i18nKey="pages.claimsPreviousLeavesIntro.needHeader"
          values={{ startDate, otherLeaveStartDate }}
        />
      </Heading>
      <div className="margin-left-4">
        <Trans
          i18nKey="pages.claimsPreviousLeavesIntro.need"
          values={{ startDate }}
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />
        <Details
          label={t(
            "pages.claimsPreviousLeavesIntro.detailsQualifyingReasonHeader"
          )}
        >
          <Trans
            i18nKey="pages.claimsPreviousLeavesIntro.detailsQualifyingReason"
            components={{
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </Details>
      </div>

      <Heading level="3">
        <Icon
          name="close"
          size={3}
          className="text-error text-middle margin-right-1 margin-top-neg-05"
        />
        <Trans i18nKey="pages.claimsPreviousLeavesIntro.dontNeedHeader" />
      </Heading>
      <div className="margin-left-4">
        <Trans
          i18nKey="pages.claimsPreviousLeavesIntro.dontNeed"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />
        <Details
          label={t("pages.claimsPreviousLeavesIntro.detailsBenefitYearHeader")}
        >
          <Trans
            i18nKey="pages.claimsPreviousLeavesIntro.detailsBenefitYear"
            components={{
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </Details>
      </div>
    </QuestionPage>
  );
};

export default withBenefitsApplication(PreviousLeavesIntro);
