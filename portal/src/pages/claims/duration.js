import Claim from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const Duration = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields, removeField } = useFormState(props.claim);
  const {
    avg_weekly_hours_worked,
    duration_type,
    hours_off_needed,
  } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  // TODO call API once API module is ready
  // const handleSave = useHandleSave(api.patchClaim, props.setClaim);
  // TODO save the API result to the claim once we have a `setClaim` function we can use
  // For now just do nothing.
  const handleSave = async () => {};

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsDuration.title")}
      onSave={handleSave}
      // TODO update with correct next route re: pregnancy
      nextPage={routes.claims.notifiedEmployer}
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
};

export default withClaim(Duration);
