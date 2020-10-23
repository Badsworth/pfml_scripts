import Claim, { WorkPattern } from "../../models/Claim";
import React, { useEffect } from "react";
import { get, isEmpty, pick, round } from "lodash";
import InputHours from "../../components/InputHours";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.work_pattern.work_pattern_days",
  "claim.hours_worked_per_week",
];

export const ScheduleVariable = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;
  const { formState, updateFields } = useFormState(initialEntries);
  const workPattern = new WorkPattern(formState.work_pattern);
  const minutes = workPattern.minutesWorkedEachWeek[0];

  // If the claim doesn't have any work pattern days pre-populate with a week
  useEffect(() => {
    const initialWorkPatternDays = get(
      initialEntries,
      "work_pattern.work_pattern_days"
    );

    if (isEmpty(initialWorkPatternDays)) {
      const { work_pattern_days } = WorkPattern.addWeek(new WorkPattern());
      updateFields({
        work_pattern: { work_pattern_days },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleHoursChange = (event) => {
    const { work_pattern_days } = WorkPattern.updateWeek(
      workPattern,
      1,
      event.target.value
    );

    updateFields({
      work_pattern: { work_pattern_days },
    });
  };

  const handleSave = async () => {
    // User may have navigated to this page from a rotating schedule
    // which has multiple weeks. Update the work_pattern_days with just
    // the first week of a variable schedule
    const work_pattern_days = workPattern.weeks[0];
    // TODO (CP-1262): refactor calculating hours worked per week to WorkPattern model
    const hours_worked_per_week = round(
      workPattern.minutesWorkedEachWeek[0] / 60,
      2
    );
    await appLogic.claims.update(claim.application_id, {
      hours_worked_per_week,
      work_pattern: { work_pattern_days },
    });
  };

  return (
    <QuestionPage
      title={t("pages.claimsScheduleVariable.title")}
      onSave={handleSave}
    >
      <InputHours
        {...getFunctionalInputProps("hours_worked_per_week")}
        label={t("pages.claimsScheduleVariable.inputHoursLabel")}
        hoursLabel={t("pages.claimsScheduleVariable.hoursLabel")}
        minutesLabel={t("pages.claimsScheduleVariable.minutesLabel")}
        value={minutes}
        minutesIncrement={15}
        onChange={handleHoursChange}
      />
    </QuestionPage>
  );
};

ScheduleVariable.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(ScheduleVariable);
