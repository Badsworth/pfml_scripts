import Claim, { OrderedDaysOfWeek, WorkPattern } from "../../models/Claim";
import React, { useEffect } from "react";
import { get, isEmpty, pick, round } from "lodash";
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
  // Include validations for minutes at any work_pattern_days index
  "claim.work_pattern.work_pattern_days[*].minutes",
];

export const ScheduleFixed = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;
  const { formState, updateFields } = useFormState(initialEntries);
  const workPattern = new WorkPattern(formState.work_pattern);

  // if work pattern days is empty, pre-populate with 7 days
  useEffect(() => {
    const initialWorkPatternDays = get(
      initialEntries,
      "work_pattern.work_pattern_days"
    );

    if (isEmpty(initialWorkPatternDays)) {
      const { work_pattern_days } = WorkPattern.addWeek(new WorkPattern());

      updateFields({ work_pattern: { work_pattern_days } });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSave = async () => {
    // User may have navigated to this page from a rotating schedule
    // which has multiple week. Update the work_pattern_days with just
    // the first week of a fixed schedule
    const work_pattern_days = workPattern.weeks[0];
    // TODO (CP-1262): refactor calculating hours worked per week to WorkPattern model
    const minutes = workPattern.minutesWorkedEachWeek[0];
    const hours_worked_per_week = round(minutes / 60, 2);

    await appLogic.claims.update(claim.application_id, {
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
  claim: PropTypes.instanceOf(Claim).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(ScheduleFixed);
