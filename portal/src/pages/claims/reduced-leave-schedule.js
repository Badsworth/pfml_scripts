import Claim, {
  LeaveReason,
  OrderedDaysOfWeek,
  WorkPattern,
} from "../../models/Claim";
import Alert from "../../components/Alert";
import Details from "../../components/Details";
import Heading from "../../components/Heading";
import InputHours from "../../components/InputHours";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import WorkPatternTable from "../../components/WorkPatternTable";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * Convenience constant for referencing the leave period object
 * and referencing fields within it
 */
const leavePeriodPath = "leave_details.reduced_schedule_leave_periods[0]";

export const fields = [
  `claim.${leavePeriodPath}.frequency_interval_basis`,
  `claim.${leavePeriodPath}.friday_off_minutes`,
  `claim.${leavePeriodPath}.leave_period_id`,
  `claim.${leavePeriodPath}.monday_off_minutes`,
  `claim.${leavePeriodPath}.saturday_off_minutes`,
  `claim.${leavePeriodPath}.sunday_off_minutes`,
  `claim.${leavePeriodPath}.thursday_off_minutes`,
  `claim.${leavePeriodPath}.tuesday_off_minutes`,
  `claim.${leavePeriodPath}.wednesday_off_minutes`,
];

export const ReducedLeaveSchedule = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const workPattern = new WorkPattern(claim.work_pattern);

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const contentContext = {
    [LeaveReason.bonding]: "bonding",
    [LeaveReason.medical]: "medical",
  }[claim.leave_details.reason];

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsReducedLeaveSchedule.title")}
      onSave={handleSave}
    >
      {claim.isMedicalLeave && (
        <Alert state="info">
          {t("pages.claimsReducedLeaveSchedule.medicalAlert")}
        </Alert>
      )}

      <Heading level="2" size="1">
        {t("pages.claimsReducedLeaveSchedule.sectionLabel")}
      </Heading>

      <Lead>
        <Trans
          i18nKey="pages.claimsReducedLeaveSchedule.lead"
          tOptions={{ context: contentContext }}
        />
      </Lead>

      <Details label={t("pages.claimsReducedLeaveSchedule.workScheduleToggle")}>
        <WorkPatternTable weeks={workPattern.weeks} />
      </Details>

      {OrderedDaysOfWeek.map((day, i) => (
        <InputHours
          {...getFunctionalInputProps(
            `${leavePeriodPath}.${day.toLowerCase()}_off_minutes`,
            { fallbackValue: null }
          )}
          label={t("pages.claimsReducedLeaveSchedule.inputHoursLabel", {
            context: day,
          })}
          smallLabel
          hoursLabel={t("pages.claimsReducedLeaveSchedule.hoursLabel")}
          minutesLabel={t("pages.claimsReducedLeaveSchedule.minutesLabel")}
          key={`input-hours-${i}`}
          minutesIncrement={15}
        />
      ))}
    </QuestionPage>
  );
};

ReducedLeaveSchedule.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(ReducedLeaveSchedule);
