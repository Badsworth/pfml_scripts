import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import LeaveReason from "../../models/LeaveReason";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.leave_details.pregnant_or_recent_birth"];

export const ReasonPregnancy = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
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
    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
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

export default withBenefitsApplication(ReasonPregnancy);
