import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Details from "../../components/core/Details";
import Heading from "../../components/core/Heading";
import IconHeading from "../../components/core/IconHeading";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import { useTranslation } from "../../locales/i18n";

export const PreviousLeavesIntro = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const startDate = formatDate(claim.leaveStartDate).full();
  const otherLeaveStartDate = formatDate(claim.otherLeaveStartDate).full();

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

      <IconHeading name="check_circle">
        <Trans
          i18nKey="pages.claimsPreviousLeavesIntro.needHeader"
          values={{ startDate, otherLeaveStartDate }}
        />
      </IconHeading>
      <Trans
        i18nKey="pages.claimsPreviousLeavesIntro.need"
        values={{ startDate }}
        components={{
          ul: <ul className="usa-list margin-left-4" />,
          li: <li />,
        }}
      />
      <div className="margin-left-4 margin-bottom-4">
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

      <IconHeading name="cancel">
        {t("pages.claimsPreviousLeavesIntro.dontNeedHeader")}
      </IconHeading>
      <Trans
        i18nKey="pages.claimsPreviousLeavesIntro.dontNeed"
        components={{
          ul: <ul className="usa-list margin-left-4" />,
          li: <li />,
        }}
      />
      <div className="margin-left-4 margin-bottom-4">
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
