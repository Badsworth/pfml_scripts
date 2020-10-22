import { get, pick, round, sum } from "lodash";
import { DateTime } from "luxon";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputHours from "../../components/InputHours";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { WorkPattern } from "../../models/Claim";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.work_pattern.work_pattern_days",
  "claim.work_pattern.pattern_start_date",
  "claim.hours_worked_per_week",
];

/**
 * Page that takes how many hours a claimant works in each week of a rotating schedule
 * and sends to API as hours / minutes per day
 */
export const ScheduleRotating = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const workPattern = new WorkPattern(formState.work_pattern);

  const workPatternWeeks = workPattern.weeks;
  const numberOfWeeks = workPatternWeeks.length;

  // Pattern start date must be a sunday and must be on or before the leave period
  // starts. Generate start date choices based on the number of rotating weeks.
  const patternStartDateChoices = workPatternWeeks.map((_, i) => {
    const date = DateTime.fromISO(claim.leaveStartDate);
    // sunday i weeks before leave start date
    const days = date.weekday + 7 * i;
    const dateChoice = date.minus({ days }).toISODate();

    return {
      checked: get(formState, "work_pattern.pattern_start_date") === dateChoice,
      label: t("pages.claimsScheduleRotating.choicePatternStartWeek", {
        context: String(i + 1),
      }),
      value: dateChoice,
    };
  });

  const handleHoursChange = (event, weekNumber) => {
    const work_pattern = WorkPattern.updateWeek(
      workPattern,
      weekNumber,
      event.target.value
    );
    const averageMinutes =
      sum(work_pattern.minutesWorkedEachWeek) / numberOfWeeks;
    const hours_worked_per_week = round(averageMinutes / 60, 2);

    updateFields({
      work_pattern: pick(work_pattern, [
        "work_pattern_days",
        "pattern_start_date",
      ]),
      hours_worked_per_week,
    });
  };

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  return (
    <QuestionPage
      title={t("pages.claimsScheduleRotating.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsScheduleRotating.inputHoursHeading")}
      </Heading>
      <Lead>{t("pages.claimsScheduleRotating.inputHoursHeadingHint")}</Lead>

      {workPattern.minutesWorkedEachWeek.map((minutes, i) => (
        <InputHours
          {...getFunctionalInputProps(
            `work_pattern.work_pattern_days[${i * 7}]`
          )}
          label={t("pages.claimsScheduleRotating.inputHoursLabel", {
            context: String(i + 1),
          })}
          smallLabel
          hoursLabel={t("pages.claimsScheduleRotating.hoursLabel")}
          minutesLabel={t("pages.claimsScheduleRotating.minutesLabel")}
          key={`input-hours-${i}`}
          value={minutes}
          minutesIncrement={15}
          onChange={(event) => handleHoursChange(event, i + 1)}
        />
      ))}

      <InputChoiceGroup
        choices={patternStartDateChoices}
        type="radio"
        label={t("pages.claimsScheduleRotating.scheduleStartDateLabel")}
        {...getFunctionalInputProps("work_pattern.pattern_start_date")}
      />
    </QuestionPage>
  );
};

ScheduleRotating.propTypes = {
  claim: PropTypes.shape({
    application_id: PropTypes.string.isRequired,
    leaveStartDate: PropTypes.string.isRequired,
    workPattern: PropTypes.instanceOf(WorkPattern),
  }).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(ScheduleRotating);
