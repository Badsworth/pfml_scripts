import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/core/Heading";
import Hint from "../../components/core/Hint";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

export const ConcurrentLeavesIntro = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const startDate = formatDate(claim.leaveStartDate).full();
  const endDate = formatDate(claim.leaveEndDate).full();

  const handleSave = async () => {
    return await appLogic.portalFlow.goToNextPage(
      { claim },
      { claim_id: claim.application_id }
    );
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
