import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const EmployerBenefitsIntro = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;

  const handleSave = () => {
    appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsEmployerBenefitsIntro.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsEmployerBenefitsIntro.sectionLabel")}
      </Heading>
    </QuestionPage>
  );
};

EmployerBenefitsIntro.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(EmployerBenefitsIntro);
