import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.pregnant_or_recent_birth"];

const ReasonPregnancy = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const handleInputChange = useHandleInputChange(updateFields);
  const { pregnant_or_recent_birth } = formState;

  const handleSave = () =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      title={t("pages.claimsReasonPregnancy.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: pregnant_or_recent_birth === true,
            label: t("pages.claimsReasonPregnancy.choiceYes"),
            value: "true",
          },
          {
            checked: pregnant_or_recent_birth === false,
            label: t("pages.claimsReasonPregnancy.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsReasonPregnancy.pregnancyOrRecentBirthLabel")}
        name="pregnant_or_recent_birth"
        onChange={handleInputChange}
        type="radio"
      />
    </QuestionPage>
  );
};

ReasonPregnancy.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(ReasonPregnancy);
