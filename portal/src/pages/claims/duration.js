import Claim from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "avg_weekly_hours_worked",
  "duration_type",
  "hours_off_needed",
];

export const Duration = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields, removeField } = useFormState(
    pick(props.claim, fields)
  );
  // TODO: use nested fields
  // https://lwd.atlassian.net/browse/CP-480
  const {
    avg_weekly_hours_worked,
    duration_type,
    hours_off_needed,
  } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = (formState) =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsDuration.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: duration_type === "continuous",
            label: t("pages.claimsDuration.continuousLabel"),
            hint: t("pages.claimsDuration.continuousHint"),
            value: "continuous",
          },
          {
            checked: duration_type === "intermittent",
            hint: t("pages.claimsDuration.intermittentHint"),
            label: t("pages.claimsDuration.intermittentLabel"),
            value: "intermittent",
          },
        ]}
        label={t("pages.claimsDuration.sectionLabel")}
        name="duration_type"
        onChange={handleInputChange}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "avg_weekly_hours_worked",
          "hours_off_needed",
        ]}
        removeField={removeField}
        visible={duration_type === "intermittent"}
      >
        <InputText
          label={t("pages.claimsDuration.avgWeeklyHoursWorkedLabel")}
          hint={t("pages.claimsDuration.avgWeeklyHoursWorkedHint")}
          name="avg_weekly_hours_worked"
          value={valueWithFallback(avg_weekly_hours_worked)}
          onChange={handleInputChange}
          width="small"
        />
        <InputText
          label={t("pages.claimsDuration.hoursOffNeededLabel")}
          hint={t("pages.claimsDuration.hoursOffNeededHint")}
          name="hours_off_needed"
          value={valueWithFallback(hours_off_needed)}
          onChange={handleInputChange}
          width="small"
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

Duration.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Duration);
