import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/Heading";
import Hint from "../../components/Hint";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { useTranslation } from "../../locales/i18n";

export const EmployerBenefitsIntro = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const handleSave = async () => {
    return await appLogic.portalFlow.goToNextPage(
      { claim },
      { claim_id: claim.application_id }
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsEmployerBenefitsIntro.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsEmployerBenefitsIntro.sectionLabel")}
      </Heading>
      <Hint>
        <Trans i18nKey="pages.claimsEmployerBenefitsIntro.intro" />
      </Hint>
    </QuestionPage>
  );
};

export default withBenefitsApplication(EmployerBenefitsIntro);
