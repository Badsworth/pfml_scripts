import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import Hint from "../../components/Hint";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const PreviousLeavesIntro = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;
  const startDate = formatDate(claim.leaveStartDate).full();

  const handleSave = () => {
    appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesIntro.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsPreviousLeavesIntro.sectionLabel")}
      </Heading>
      <Hint>
        <Trans
          i18nKey="pages.claimsPreviousLeavesIntro.intro"
          values={{ startDate }}
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />
      </Hint>
    </QuestionPage>
  );
};

PreviousLeavesIntro.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(PreviousLeavesIntro);
