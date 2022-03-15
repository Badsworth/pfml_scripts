import React, { useEffect } from "react";
import { cloneDeep, get, pick, set } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/core/Heading";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputDate from "../../components/core/InputDate";
import Lead from "../../components/core/Lead";
import LeaveReason from "../../models/LeaveReason";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import dayjs from "dayjs";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDate from "src/utils/formatDate";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

/**
 * Convenience constant for referencing the leave period object
 * and referencing fields within it
 */
const leavePeriodsListPath = "leave_details.continuous_leave_periods";
const leavePeriodPath = "leave_details.continuous_leave_periods[0]";

export const fields = [
  "claim.has_continuous_leave_periods",
  `claim.${leavePeriodPath}.end_date`,
  `claim.${leavePeriodPath}.start_date`,
];

export const LeavePeriodContinuous = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );
  const { loadCrossedBenefitYears, getCrossedBenefitYear } =
    appLogic.benefitYears;

  const employeeId = get(claim, "employee_id");
  const submissionWindow = dayjs().add(60, "day").format("YYYY-MM-DD");

  const startDate = String(get(formState, `${leavePeriodPath}.start_date`));
  const endDate = String(get(formState, `${leavePeriodPath}.end_date`));

  useEffect(() => {
    if (employeeId != null) {
      // make sure startDate & endDate are both valid dates before making the API call
      const validDateRegex = /([0-9]{4})-(?:[0-9]{2})-([0-9]{2})/;
      const validStartDate =
        startDate.match(validDateRegex) !== null &&
        !isNaN(new Date(startDate).getDate());
      const validEndDate =
        endDate.match(validDateRegex) !== null &&
        !isNaN(new Date(endDate).getDate());
      if (validStartDate && validEndDate) {
        loadCrossedBenefitYears(employeeId, startDate, endDate);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeId, startDate, endDate]);

  const crossedBenefitYear = getCrossedBenefitYear();
  const canSubmitBoth =
    crossedBenefitYear !== null &&
    crossedBenefitYear.benefit_year_end_date <= submissionWindow;

  /**
   * When user indicates they have this leave period type,
   * add a blank leave period so validations are ran against it
   */
  useEffect(() => {
    const existingLeavePeriod = get(formState, leavePeriodPath);

    if (formState.has_continuous_leave_periods && !existingLeavePeriod) {
      updateFields({ [leavePeriodPath]: {} });
    }
  }, [formState, updateFields]);

  const handleSave = async () => {
    /**
     * We need to include the leave_period_id if one exists, so the
     * API merges changes, rather than creates a different leave period.
     * We access this ID from the `claim` prop, rather than including it
     * as part of our initial form state, because there are scenarios where a
     * leave period can be created and not reflected back in our form state,
     * such as when the user has validation issues when initially submitting
     * the page.
     */
    const leave_period_id = get(claim, `${leavePeriodPath}.leave_period_id`);
    const requestData = cloneDeep(formState);

    if (formState.has_continuous_leave_periods && leave_period_id) {
      set(requestData, `${leavePeriodPath}.leave_period_id`, leave_period_id);
    }

    await appLogic.benefitsApplications.update(
      claim.application_id,
      requestData
    );
  };

  const contentContext = findKeyByValue(
    LeaveReason,
    claim.leave_details.reason
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsLeavePeriodContinuous.title")}
      onSave={handleSave}
    >
      {(claim.isMedicalOrPregnancyLeave || claim.isCaringLeave) && (
        <Alert state="info" neutral>
          <Trans
            i18nKey="pages.claimsLeavePeriodContinuous.needDocumentAlert"
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
              context: contentContext,
            }}
          />
        </Alert>
      )}

      <InputChoiceGroup
        {...getFunctionalInputProps("has_continuous_leave_periods")}
        choices={[
          {
            checked: formState.has_continuous_leave_periods === true,
            label: t("pages.claimsLeavePeriodContinuous.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_continuous_leave_periods === false,
            label: t("pages.claimsLeavePeriodContinuous.choiceNo"),
            value: "false",
          },
        ]}
        hint={
          claim.isMedicalOrPregnancyLeave || claim.isCaringLeave
            ? t("pages.claimsLeavePeriodContinuous.hasLeaveHint", {
                context: contentContext,
              })
            : null
        }
        label={t("pages.claimsLeavePeriodContinuous.hasLeaveLabel")}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={[leavePeriodsListPath]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
        visible={formState.has_continuous_leave_periods}
      >
        <Heading level="2" size="1">
          {t("pages.claimsLeavePeriodContinuous.datesSectionLabel")}
        </Heading>

        <Lead>
          <Trans
            i18nKey="pages.claimsLeavePeriodContinuous.datesLead"
            tOptions={{
              context: contentContext,
            }}
          />
        </Lead>

        <InputDate
          {...getFunctionalInputProps(`${leavePeriodPath}.start_date`)}
          label={t("pages.claimsLeavePeriodContinuous.startDateLabel")}
          example={t("components.form.dateInputExample")}
          dayLabel={t("components.form.dateInputDayLabel")}
          monthLabel={t("components.form.dateInputMonthLabel")}
          yearLabel={t("components.form.dateInputYearLabel")}
          smallLabel
        />
        <InputDate
          {...getFunctionalInputProps(`${leavePeriodPath}.end_date`)}
          label={t("pages.claimsLeavePeriodContinuous.endDateLabel")}
          example={t("components.form.dateInputExample")}
          dayLabel={t("components.form.dateInputDayLabel")}
          monthLabel={t("components.form.dateInputMonthLabel")}
          yearLabel={t("components.form.dateInputYearLabel")}
          smallLabel
        />

        {crossedBenefitYear !== null && canSubmitBoth && (
          <Alert
            state="info"
            heading={t("shared.crossedBenefitYear.header")}
            autoWidth
          >
            <Trans
              i18nKey="shared.crossedBenefitYear.submittingBoth"
              components={{
                b: <b />,
                ul: <ul className="usa-list" />,
                li: <li />,
                "benefits-amount-link": (
                  <a
                    href={
                      routes.external.massgov.benefitsGuide_weeklyBenefitAmounts
                    }
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                "terms-to-know-link": (
                  <a
                    href={routes.external.massgov.importantTermsToKnow}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                "waiting-week-link": (
                  <a
                    href={routes.external.massgov.sevenDayWaitingPeriodInfo}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
              }}
              values={{
                benefitYearStartDate: formatDate(
                  crossedBenefitYear.benefit_year_start_date
                ).short(),
                benefitYearEndDate: formatDate(
                  crossedBenefitYear.benefit_year_end_date
                ).short(),
                newBenefitYearStartDate: formatDate(
                  dayjs(crossedBenefitYear.benefit_year_end_date)
                    .add(1, "day")
                    .format("YYYY-MM-DD")
                ).short(),
                leaveStartDate: formatDate(startDate).short(),
                leaveEndDate: formatDate(endDate).short(),
              }}
            />
          </Alert>
        )}
        {crossedBenefitYear !== null && !canSubmitBoth && (
          <Alert
            state="info"
            heading={t("shared.crossedBenefitYear.header")}
            autoWidth
          >
            <Trans
              i18nKey="shared.crossedBenefitYear.submittingOne_leaveDetails"
              components={{
                b: <b />,
                ul: <ul className="usa-list" />,
                li: <li />,
                "terms-to-know-link": (
                  <a
                    href={routes.external.massgov.importantTermsToKnow}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
              }}
              values={{
                benefitYearStartDate: formatDate(
                  crossedBenefitYear.benefit_year_start_date
                ).short(),
                benefitYearEndDate: formatDate(
                  crossedBenefitYear.benefit_year_end_date
                ).short(),
                newBenefitYearStartDate: formatDate(
                  dayjs(crossedBenefitYear.benefit_year_end_date)
                    .add(1, "day")
                    .format("YYYY-MM-DD")
                ).short(),
                leaveStartDate: formatDate(startDate).short(),
                leaveEndDate: formatDate(endDate).short(),
                applicationSubmissionDate: formatDate(
                  dayjs(crossedBenefitYear.benefit_year_end_date)
                    .add(1, "day")
                    .subtract(60, "day")
                    .format("YYYY-MM-DD")
                ).short(),
              }}
            />
          </Alert>
        )}
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(LeavePeriodContinuous);
