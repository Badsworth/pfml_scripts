import React, { useState } from "react";
import { WorkPattern, WorkPatternDay } from "../../models/BenefitsApplication";
import { pick, round } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/core/Heading";
import InputHours from "../../components/core/InputHours";
import Lead from "../../components/core/Lead";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import isBlank from "../../utils/isBlank";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.work_pattern.work_pattern_days",
  // Include validations for maximum minutes worked in a week
  // If minutes worked in a week are greater than the minutes in a calendar week (10080),
  // the minutes allocated to the first day will always be over 1440
  // and return a validation error.
  "claim.work_pattern.work_pattern_days[0].minutes",
];

export const ScheduleVariable = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const workPattern = new WorkPattern(claim.work_pattern || {});

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  // minutesWorkedPerWeek will be spread across
  // 7 work_pattern_days when user submits and is not a part of the Claim model.
  const [minutesWorkedPerWeek, setMinutesWorkedPerWeek] = useState(
    workPattern.minutesWorkedPerWeek
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const handleHoursChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const minutesStr = event.target.value;

    // The input is coerced into a string by InputHours.js
    // Set it to null instead of "" to clear the input field
    const minutes = minutesStr === "" ? null : parseInt(minutesStr);

    setMinutesWorkedPerWeek(minutes);
  };

  const handleSave = async () => {
    let work_pattern_days: WorkPatternDay[] | null = null;
    let hours_worked_per_week: null | number = null;

    if (isBlank(minutesWorkedPerWeek)) {
      work_pattern_days = [];
    } else {
      ({ work_pattern_days } =
        WorkPattern.createWithWeek(minutesWorkedPerWeek));
      hours_worked_per_week = round(minutesWorkedPerWeek / 60, 2);
    }

    await appLogic.benefitsApplications.update(claim.application_id, {
      hours_worked_per_week,
      work_pattern: {
        work_pattern_days,
      },
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

      <Lead>
        <Trans
          i18nKey="pages.claimsScheduleVariable.lead"
          components={{
            "calculate-hours-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.calculateHours}
              />
            ),
          }}
        />
      </Lead>
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

export default withBenefitsApplication(ScheduleVariable);
