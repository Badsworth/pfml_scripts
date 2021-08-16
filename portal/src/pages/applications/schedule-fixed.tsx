import BenefitsApplication, {
  OrderedDaysOfWeek,
  WorkPattern,
} from "../../models/BenefitsApplication";
import { get, pick, round } from "lodash";
import Heading from "../../components/Heading";
import InputHours from "../../components/InputHours";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.work_pattern.work_pattern_days",
  // Include validations for minutes at any work_pattern_days index
  "claim.work_pattern.work_pattern_days[*].minutes",
];

export const ScheduleFixed = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState(
    Object.assign(
      initialEntries,
      // Ensure initial work_pattern has 7 empty days by using
      // the WorkPattern model which defaults empty work_pattern_days to 7 empty days
      { work_pattern: new WorkPattern(initialEntries.work_pattern) }
    )
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSave = async () => {
    const workPattern = new WorkPattern(formState.work_pattern);
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'work_pattern_days' does not exist on typ... Remove this comment to see the full error message
    const { work_pattern_days } = workPattern;
    // TODO (CP-1262): refactor calculating hours worked per week to WorkPattern model
    const minutes = workPattern.minutesWorkedPerWeek;
    const hours_worked_per_week = round(minutes / 60, 2);

    await appLogic.benefitsApplications.update(claim.application_id, {
      hours_worked_per_week,
      work_pattern: { work_pattern_days },
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

ScheduleFixed.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(ScheduleFixed);
