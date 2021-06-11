import React, { useEffect } from "react";
import { cloneDeep, get, pick, set } from "lodash";
import Alert from "../../components/Alert";
import BenefitsApplication from "../../models/BenefitsApplication";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import Lead from "../../components/Lead";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

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

export const LeavePeriodContinuous = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );

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
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsLeavePeriodContinuous.title")}
      onSave={handleSave}
    >
      {(claim.isMedicalLeave || claim.isCaringLeave) && (
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
          claim.isMedicalLeave || claim.isCaringLeave
            ? t("pages.claimsLeavePeriodContinuous.hasLeaveHint", {
                context:
                  claim.isMedicalLeave &&
                  isFeatureEnabled("updateMedicalCertForm")
                    ? "updateMedicalCertForm"
                    : contentContext,
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
              context:
                claim.isMedicalLeave &&
                isFeatureEnabled("updateMedicalCertForm")
                  ? "updateMedicalCertForm"
                  : contentContext,
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
      </ConditionalContent>
    </QuestionPage>
  );
};

LeavePeriodContinuous.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withBenefitsApplication(LeavePeriodContinuous);
