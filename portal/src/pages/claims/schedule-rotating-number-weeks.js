import { WorkPattern, WorkPatternType } from "../../models/Claim";
import { pick, range } from "lodash";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.work_pattern.work_pattern_days"];

/**
 * Page that creates 7 empty work_pattern_days for every rotating week
 */
export const ScheduleRotatingNumberWeeks = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const workPattern = new WorkPattern(formState.work_pattern);

  const numberOfWeeks = workPattern.weeks.length;

  // A user may select a `rotating` schedule on the previous page but actually
  // intend to select `variable`. The radio choice allows the user to correct
  // their work pattern type and be routed to the /schedule-variable page
  //
  // This handler resets the `work_pattern_days` and `pattern_start_date` on each change.
  const handleChange = (event) => {
    let { value } = event.target;
    let work_pattern_type = WorkPatternType.rotating;

    if (value === WorkPatternType.variable) {
      work_pattern_type = WorkPatternType.variable;
      // default variable schedules to 1 week
      // this would typically happen on the /schedule-variable page
      // but we are creating it here since this page also validates
      // for required work_pattern_days
      value = "1";
    }

    let work_pattern = new WorkPattern({
      work_pattern_type,
      pattern_start_date: null,
    });

    range(value).forEach(() => {
      work_pattern = WorkPattern.addWeek(work_pattern);
    });

    updateFields({
      // if a user has already filled their hours_worked_per_week or pattern_start_date
      // but navigates back to this page, we need to reset that data to keep it
      // in sync with total weeks / hours across work_pattern_days.
      hours_worked_per_week: null,
      work_pattern,
    });
  };

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  return (
    <QuestionPage
      title={t("pages.claimsScheduleRotating.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("work_pattern.work_pattern_days")}
        choices={[
          {
            checked: numberOfWeeks === 2,
            label: t("pages.claimsScheduleRotatingNumberWeeks.choice2Weeks"),
            value: "2",
          },
          {
            checked: numberOfWeeks === 3,
            label: t("pages.claimsScheduleRotatingNumberWeeks.choice3Weeks"),
            value: "3",
          },
          {
            checked: numberOfWeeks === 4,
            label: t("pages.claimsScheduleRotatingNumberWeeks.choice4Weeks"),
            value: "4",
          },
          {
            checked: workPattern.work_pattern_type === WorkPatternType.variable,
            label: t(
              "pages.claimsScheduleRotatingNumberWeeks.choiceMoreThan4Weeks"
            ),
            value: WorkPatternType.variable,
          },
        ]}
        value={numberOfWeeks}
        label={t("pages.claimsScheduleRotatingNumberWeeks.howManyWeeksLabel")}
        type="radio"
        onChange={handleChange}
      />
    </QuestionPage>
  );
};

ScheduleRotatingNumberWeeks.propTypes = {
  claim: PropTypes.shape({
    application_id: PropTypes.string.isRequired,
  }).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(ScheduleRotatingNumberWeeks);
