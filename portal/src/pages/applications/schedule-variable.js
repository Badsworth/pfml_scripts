import BenefitsApplication, {
  WorkPattern,
} from "../../models/BenefitsApplication";
import React, { useState } from "react";
import { pick, round } from "lodash";
import Heading from "../../components/Heading";
import InputHours from "../../components/InputHours";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

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
    workPattern.minutesWorkedPerWeek
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleHoursChange = (event) => {
    const minutesStr = event.target.value;

    // The input is coerced into a string by InputHours.js
    // Set it to null instead of "" to clear the input field
    const minutes = minutesStr === "" ? null : parseInt(minutesStr);

    setMinutesWorkedPerWeek(minutes);
  };

  const handleSave = async () => {
    let work_pattern_days;
    let hours_worked_per_week = null;

    if (!minutesWorkedPerWeek) {
      work_pattern_days = [];
    } else {
      ({ work_pattern_days } = WorkPattern.createWithWeek(
        minutesWorkedPerWeek
      ));
      hours_worked_per_week = round(minutesWorkedPerWeek / 60, 2);
    }

    await appLogic.benefitsApplications.update(claim.application_id, {
      hours_worked_per_week,
      work_pattern: { work_pattern_days },
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

ScheduleVariable.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(ScheduleVariable);
