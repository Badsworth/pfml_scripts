import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import Hint from "../../components/Hint";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { formatDate } from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const ConcurrentLeavesIntro = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;

  const startDate = formatDate(claim.leaveStartDate);
  const endDate = formatDate(claim.leaveEndDate);

  const handleSave = () => {
    appLogic.portalFlow.goToNextPage({ claim }, query);
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
          values={{
            startDate,
            endDate,
          }}
        />
      </Hint>
    </QuestionPage>
  );
};

ConcurrentLeavesIntro.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(ConcurrentLeavesIntro);
