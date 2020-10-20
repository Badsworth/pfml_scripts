import Claim, {
  WorkPatternType as WorkPatternTypeEnum,
} from "../../models/Claim";
import { get, pick } from "lodash";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.work_pattern.work_pattern_type"];

export const WorkPatternType = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const work_pattern_type = get(formState, "work_pattern.work_pattern_type");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

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
        choices={["fixed", "variable", "rotating"].map((key) => ({
          checked: work_pattern_type === WorkPatternTypeEnum[key],
          hint:
            key === "rotating"
              ? t("pages.claimsWorkPatternType.choiceHint", {
                  context: key,
                })
              : null,
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
  claim: PropTypes.instanceOf(Claim).isRequired,
};

export default withClaim(WorkPatternType);
