import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

// TODO (CP-1958): Confirm these field names
export const fields = ["claim.family_member.date_of_birth"];

export const FamilyMemberDateOfBirth = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;

  const handleSave = (event) => {
    appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsLeaveReason.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsFamilyMemberDateOfBirth.sectionLabel")}
      </Heading>
    </QuestionPage>
  );
};

FamilyMemberDateOfBirth.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(FamilyMemberDateOfBirth);
