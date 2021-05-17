import BenefitsApplication, {
  OrderedDaysOfWeek,
  ReducedScheduleLeavePeriod,
  WorkPattern,
  WorkPatternType,
} from "../../models/BenefitsApplication";
import { get, pick, set, zip } from "lodash";
import Alert from "../../components/Alert";
import Details from "../../components/Details";
import Heading from "../../components/Heading";
import InputHours from "../../components/InputHours";
import Lead from "../../components/Lead";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import WeeklyTimeTable from "../../components/WeeklyTimeTable";
import convertMinutesToHours from "../../utils/convertMinutesToHours";
import findKeyByValue from "../../utils/findKeyByValue";
import routes from "../../routes";
import spreadMinutesOverWeek from "../../utils/spreadMinutesOverWeek";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

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

  const initialClaimState = pick(props, fields).claim;
  const initialLeavePeriod = new ReducedScheduleLeavePeriod(
    get(claim, leavePeriodPath)
  );
  const workPattern = new WorkPattern(claim.work_pattern);
  const gatherMinutesAsWeeklyAverage =
    workPattern.work_pattern_type === WorkPatternType.variable;

  const { formState, updateFields } = useFormState({
    ...initialClaimState,
    totalMinutesOff: gatherMinutesAsWeeklyAverage
      ? initialLeavePeriod.totalMinutesOff
      : undefined,
  });

  const handleSave = () => {
    const { totalMinutesOff, ...dailyMinutesOff } = formState;
    const requestData = dailyMinutesOff;

    if (gatherMinutesAsWeeklyAverage) {
      // Still need to store time in the API in individual day fields:
      const dailyMinutes = !totalMinutesOff
        ? [null, null, null, null, null, null, null]
        : spreadMinutesOverWeek(totalMinutesOff);
      const minuteFields = [
        `${leavePeriodPath}.sunday_off_minutes`,
        `${leavePeriodPath}.monday_off_minutes`,
        `${leavePeriodPath}.tuesday_off_minutes`,
        `${leavePeriodPath}.wednesday_off_minutes`,
        `${leavePeriodPath}.thursday_off_minutes`,
        `${leavePeriodPath}.friday_off_minutes`,
        `${leavePeriodPath}.saturday_off_minutes`,
      ];

      zip(minuteFields, dailyMinutes).forEach(([field, minutes]) => {
        set(requestData, field, minutes);
      });
    }

    return appLogic.benefitsApplications.update(
      claim.application_id,
      requestData
    );
  };

  const contentReasonContext = findKeyByValue(
    LeaveReason,
    claim.leave_details.reason
  );

  const contentScheduleTypeContext = findKeyByValue(
    WorkPatternType,
    workPattern.work_pattern_type
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // Common props shared across InputHours components regardless of work pattern type
  const inputHoursProps = {
    smallLabel: true,
    hoursLabel: t("pages.claimsReducedLeaveSchedule.hoursLabel"),
    minutesLabel: t("pages.claimsReducedLeaveSchedule.minutesLabel"),
    minutesIncrement: 15,
  };

  return (
    <QuestionPage
      title={t("pages.claimsReducedLeaveSchedule.title")}
      onSave={handleSave}
    >
      {(claim.isMedicalLeave || claim.isCaringLeave) && (
        <Alert state="info" neutral>
          <Trans
            i18nKey="pages.claimsReducedLeaveSchedule.needDocumentAlert"
            components={{
              "healthcare-provider-form-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.healthcareProviderForm}
                />
              ),
              "caregiver-certification-form-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.caregiverCertificationForm}
                />
              ),
            }}
            tOptions={{
              context: contentReasonContext,
            }}
          />
        </Alert>
      )}

      <Heading level="2" size="1">
        {t("pages.claimsReducedLeaveSchedule.sectionLabel", {
          context: contentScheduleTypeContext,
        })}
      </Heading>

      <Lead>
        <Trans
          i18nKey="pages.claimsReducedLeaveSchedule.lead"
          tOptions={{ context: contentReasonContext }}
        />
      </Lead>

      <Details label={t("pages.claimsReducedLeaveSchedule.workScheduleToggle")}>
        {gatherMinutesAsWeeklyAverage ? (
          t("pages.claimsReview.workPatternVariableTime", {
            context:
              convertMinutesToHours(workPattern.minutesWorkedPerWeek)
                .minutes === 0
                ? "noMinutes"
                : null,
            ...convertMinutesToHours(workPattern.minutesWorkedPerWeek),
          })
        ) : (
          <WeeklyTimeTable days={workPattern.work_pattern_days} />
        )}
      </Details>

      {gatherMinutesAsWeeklyAverage && (
        <InputHours
          {...getFunctionalInputProps("totalMinutesOff", {
            fallbackValue: null,
          })}
          label={t("pages.claimsReducedLeaveSchedule.inputHoursLabel", {
            context: "weekly",
          })}
          {...inputHoursProps}
        />
      )}

      {!gatherMinutesAsWeeklyAverage &&
        OrderedDaysOfWeek.map((day, i) => (
          <InputHours
            {...getFunctionalInputProps(
              `${leavePeriodPath}.${day.toLowerCase()}_off_minutes`,
              { fallbackValue: null }
            )}
            label={t("pages.claimsReducedLeaveSchedule.inputHoursLabel", {
              context: day,
            })}
            key={`input-hours-${i}`}
            {...inputHoursProps}
          />
        ))}
    </QuestionPage>
  );
};

ReducedLeaveSchedule.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withBenefitsApplication(ReducedLeaveSchedule);
