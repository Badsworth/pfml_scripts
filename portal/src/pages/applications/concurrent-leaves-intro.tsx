import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import Hint from "../../components/Hint";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

interface ConcurrentLeavesIntroProps {
  appLogic: AppLogic;
  claim: BenefitsApplication;
  query: Record<string, string>;
}

export const ConcurrentLeavesIntro = (props: ConcurrentLeavesIntroProps) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;

  const startDate = formatDate(claim.leaveStartDate).full();
  const endDate = formatDate(claim.leaveEndDate).full();

  const handleSave = async () => {
    return await appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsConcurrentLeavesIntro.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsConcurrentLeavesIntro.sectionLabel")}
      </Heading>
      <Hint>
        <Trans
          i18nKey="pages.claimsConcurrentLeavesIntro.intro"
          components={{
            "examples-of-using-paid-leave": (
              <a
                href={routes.external.massgov.usingAccruedPaidLeave}
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
          }}
          values={{
            startDate,
            endDate,
          }}
        />
      </Hint>
    </QuestionPage>
  );
};

export default withBenefitsApplication(ConcurrentLeavesIntro);
