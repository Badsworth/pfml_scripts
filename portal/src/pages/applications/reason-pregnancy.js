import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.leave_details.pregnant_or_recent_birth"];

export const ReasonPregnancy = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const pregnancyOrRecentBirth = get(
    formState,
    "leave_details.pregnant_or_recent_birth"
  );

  const handleSave = () => {
    if (pregnancyOrRecentBirth) {
      formState.leave_details.reason = LeaveReason.pregnancy;
    } else if (pregnancyOrRecentBirth === false) {
      formState.leave_details.reason = LeaveReason.medical;
    }
    appLogic.benefitsApplications.update(claim.application_id, formState);
  };
  return (
    <QuestionPage
      title={t("pages.claimsReasonPregnancy.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("leave_details.pregnant_or_recent_birth")}
        choices={[
          {
            checked: pregnancyOrRecentBirth === true,
            label: t("pages.claimsReasonPregnancy.choiceYes"),
            value: "true",
          },
          {
            checked: pregnancyOrRecentBirth === false,
            label: t("pages.claimsReasonPregnancy.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsReasonPregnancy.pregnancyOrRecentBirthLabel")}
        type="radio"
      />
    </QuestionPage>
  );
};

ReasonPregnancy.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withBenefitsApplication(ReasonPregnancy);
