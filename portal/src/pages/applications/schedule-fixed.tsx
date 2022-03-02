import {
  OrderedDaysOfWeek,
  WorkPattern,
} from "../../models/BenefitsApplication";
import { get, pick, round } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/core/Heading";
import InputHours from "../../components/core/InputHours";
import Lead from "../../components/core/Lead";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import isBlank from "../../utils/isBlank";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.work_pattern.work_pattern_days",
  // Include validations for minutes at any work_pattern_days index
  "claim.work_pattern.work_pattern_days[*].minutes",
];

export const ScheduleFixed = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;

  const { formState, updateFields } = useFormState(
    Object.assign(
      initialEntries,
      // Ensure initial work_pattern has 7 empty days by using
      // the WorkPattern model which defaults empty work_pattern_days to 7 empty days
      { work_pattern: new WorkPattern(initialEntries?.work_pattern || {}) }
    )
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const handleSave = async () => {
    const workPattern = new WorkPattern(formState.work_pattern);
    const { work_pattern_days } = workPattern;
    // TODO (CP-1262): refactor calculating hours worked per week to WorkPattern model
    const minutes = workPattern.minutesWorkedPerWeek;
    const hours_worked_per_week = isBlank(minutes)
      ? null
      : round(minutes / 60, 2);

    await appLogic.benefitsApplications.update(claim.application_id, {
      hours_worked_per_week,
      work_pattern: {
        work_pattern_days,
      },
    });
  };

  return (
    <QuestionPage
      title={t("pages.claimsScheduleFixed.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsScheduleFixed.inputHoursHeading")}
      </Heading>
      <Lead>{t("pages.claimsScheduleFixed.inputHoursHeadingHint")}</Lead>

      {OrderedDaysOfWeek.map((day, i) => (
        <InputHours
          {...getFunctionalInputProps(
            `work_pattern.work_pattern_days[${i}].minutes`
          )}
          label={t("pages.claimsScheduleFixed.inputHoursLabel", {
            context: day,
          })}
          smallLabel
          hoursLabel={t("pages.claimsScheduleFixed.hoursLabel")}
          minutesLabel={t("pages.claimsScheduleFixed.minutesLabel")}
          key={`input-hours-${i}`}
          value={get(formState, `work_pattern.work_pattern_days[${i}].minutes`)}
          minutesIncrement={15}
        />
      ))}
    </QuestionPage>
  );
};

export default withBenefitsApplication(ScheduleFixed);
