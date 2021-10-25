import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import Hint from "../../components/Hint";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

interface EmployerBenefitsIntroProps {
  appLogic: AppLogic;
  claim: BenefitsApplication;
  query: Record<string, string>;
}

export const EmployerBenefitsIntro = (props: EmployerBenefitsIntroProps) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;

  const handleSave = async () => {
    return await appLogic.portalFlow.goToNextPage({ claim }, query);
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
