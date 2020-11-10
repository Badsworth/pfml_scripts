import Claim, { WorkPattern } from "../../models/Claim";
import React, { useState } from "react";
import { isEmpty, pick, round } from "lodash";
import Heading from "../../components/Heading";
import InputHours from "../../components/InputHours";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.work_pattern.work_pattern_days",
  // Include validations for maximum minutes worked in a week
  // If minutes worked in a week are greater than the minutes in a calendar week (10080),
  // the minutes allocated to the first day will always be over 1440
  // and return a validation error.
  "claim.work_pattern.work_pattern_days[0].minutes",
];

export const ScheduleVariable = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const workPattern = new WorkPattern(claim.work_pattern);
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  // minutesWorkedPerWeek will be spread across
  // 7 work_pattern_days when user submits and is not a part of the Claim model.
  const [minutesWorkedPerWeek, setMinutesWorkedPerWeek] = useState(
    workPattern.minutesWorkedEachWeek[0]
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleHoursChange = (event) => {
    setMinutesWorkedPerWeek(event.target.value);
  };

  const handleSave = async () => {
    let workPattern = new WorkPattern(formState.work_pattern);

    if (isEmpty(workPattern.work_pattern_days)) {
      workPattern = WorkPattern.addWeek(workPattern, minutesWorkedPerWeek);
    } else {
      workPattern = WorkPattern.updateWeek(
        workPattern,
        1,
        minutesWorkedPerWeek
      );
    }

    const hours_worked_per_week = round(minutesWorkedPerWeek / 60, 2);
    await appLogic.claims.update(claim.application_id, {
      hours_worked_per_week,
      work_pattern: { work_pattern_days: workPattern.weeks[0] },
    });
  };

  return (
    <QuestionPage
      title={t("pages.claimsScheduleVariable.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsScheduleVariable.heading")}
      </Heading>

      <Lead>{t("pages.claimsScheduleVariable.lead")}</Lead>
      <p className="usa-hint margin-top-0 text-base-darkest">
        {t("pages.claimsScheduleVariable.hint")}
      </p>
      <InputHours
        {...getFunctionalInputProps(
          "work_pattern.work_pattern_days[0].minutes"
        )}
        label={t("pages.claimsScheduleVariable.inputHoursLabel")}
        hoursLabel={t("pages.claimsScheduleVariable.hoursLabel")}
        minutesLabel={t("pages.claimsScheduleVariable.minutesLabel")}
        value={minutesWorkedPerWeek}
        onChange={handleHoursChange}
        smallLabel
        minutesIncrement={15}
      />
    </QuestionPage>
  );
};

ScheduleVariable.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(ScheduleVariable);
