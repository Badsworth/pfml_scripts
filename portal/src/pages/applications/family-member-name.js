import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

// TODO (CP-1956): Confirm these field names
export const fields = [
  "claim.family_member.first_name",
  "claim.family_member.middle_name",
  "claim.family_member.last_name",
];

export const FamilyMemberName = (props) => {
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
        {t("pages.claimsFamilyMemberName.sectionLabel")}
      </Heading>
    </QuestionPage>
  );
};

FamilyMemberName.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withClaim(FamilyMemberName);
