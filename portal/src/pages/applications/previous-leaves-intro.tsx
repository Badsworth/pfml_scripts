import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/Heading";
import IconHeading from "../../components/IconHeading";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import { useTranslation } from "../../locales/i18n";

export const PreviousLeavesIntro = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const startDate = formatDate(claim.leaveStartDate).full();

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
          i18nKey="pages.claimsPreviousLeavesIntro.introHeader"
          values={{ startDate }}
        />
      </IconHeading>
      <Trans
        i18nKey="pages.claimsPreviousLeavesIntro.intro"
        values={{ startDate }}
        components={{
          ul: <ul className="usa-list margin-left-2" />,
          li: <li />,
        }}
      />
      <br />
      <IconHeading name="cancel">
        {t("pages.claimsPreviousLeavesIntro.introDontNeedHeader")}
      </IconHeading>
      <Trans
        i18nKey="pages.claimsPreviousLeavesIntro.introDontNeed"
        values={{ startDate }}
        components={{
          ul: <ul className="usa-list margin-left-2" />,
          li: <li />,
        }}
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(PreviousLeavesIntro);
