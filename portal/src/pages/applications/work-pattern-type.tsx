import BenefitsApplication, {
  WorkPatternType as WorkPatternTypeEnum,
} from "../../models/BenefitsApplication";
import { get, pick, set } from "lodash";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.work_pattern.work_pattern_type"];

export const WorkPatternType = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const work_pattern_type = get(formState, "work_pattern.work_pattern_type");

  const handleSave = async () => {
    const patchData = { ...formState };

    // if a user navigates back to this page after filling hours for
    // a work pattern type, we need to reset work_patterns_days
    // and hours_worked_per_week to null if the work_pattern_type changes
    if (work_pattern_type !== get(claim, "work_pattern.work_pattern_type")) {
      set(patchData, "hours_worked_per_week", null);
      set(patchData, "work_pattern.work_pattern_days", []);
    }

    await appLogic.benefitsApplications.update(claim.application_id, patchData);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsWorkPatternType.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("work_pattern.work_pattern_type")}
        choices={["fixed", "variable"].map((key) => ({
          checked: work_pattern_type === WorkPatternTypeEnum[key],
          hint: t("pages.claimsWorkPatternType.choiceHint", {
            context: key,
          }),
          label: t("pages.claimsWorkPatternType.choiceLabel", {
            context: key,
          }),
          value: WorkPatternTypeEnum[key],
        }))}
        label={t("pages.claimsWorkPatternType.sectionLabel")}
        type="radio"
      />
    </QuestionPage>
  );
};

WorkPatternType.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(WorkPatternType);
