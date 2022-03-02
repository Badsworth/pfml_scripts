import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/core/Heading";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import formatDate from "../../utils/formatDate";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.has_previous_leaves_same_reason"];

export const PreviousLeavesSameReason = (
  props: WithBenefitsApplicationProps
) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const leaveStartDate = formatDate(claim.leaveStartDate).full();
  const previousLeaveStartDate = formatDate(
    claim.computed_start_dates.same_reason
  ).full();

  const handleSave = () => {
    const patchData = { ...formState };
    if (
      patchData.has_previous_leaves_same_reason === false &&
      get(claim, "previous_leaves_same_reason.length")
    ) {
      patchData.previous_leaves_same_reason = null;
    }
    return appLogic.benefitsApplications.update(
      claim.application_id,
      patchData
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesSameReason.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_previous_leaves_same_reason")}
        type="radio"
        choices={[
          {
            checked: formState.has_previous_leaves_same_reason === true,
            label: t("pages.claimsPreviousLeavesSameReason.choiceYes"),
            value: "true",
            hint: t("pages.claimsPreviousLeavesSameReason.hintYes"),
          },
          {
            checked: formState.has_previous_leaves_same_reason === false,
            label: t("pages.claimsPreviousLeavesSameReason.choiceNo"),
            value: "false",
            hint: t("pages.claimsPreviousLeavesSameReason.hintNo"),
          },
        ]}
        label={
          <Heading level="2" size="1">
            {t("pages.claimsPreviousLeavesSameReason.sectionLabel", {
              previousLeaveStartDate,
              leaveStartDate,
            })}
          </Heading>
        }
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(PreviousLeavesSameReason);
