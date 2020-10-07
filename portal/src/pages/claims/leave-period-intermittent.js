import Claim, {
  IntermittentLeavePeriod,
  LeaveReason,
} from "../../models/Claim";
import React, { useEffect } from "react";
import { get, pick } from "lodash";
import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.has_intermittent_leave_periods",
  "claim.leave_details.intermittent_leave_periods[0].end_date",
  "claim.leave_details.intermittent_leave_periods[0].start_date",
  "claim.leave_details.intermittent_leave_periods[0].leave_period_id",
];

export const LeavePeriodIntermittent = (props) => {
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
    const existingLeavePeriod = get(
      formState,
      "leave_details.intermittent_leave_periods[0]"
    );

    if (formState.has_intermittent_leave_periods && !existingLeavePeriod) {
      updateFields({
        "leave_details.intermittent_leave_periods[0]": new IntermittentLeavePeriod(),
      });
    }
  }, [formState, updateFields]);

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const contentContext = {
    [LeaveReason.bonding]: "bonding",
    [LeaveReason.medical]: "medical",
  }[claim.leave_details.reason];

  const hasOtherLeavePeriodTypes =
    claim.isContinuous || claim.isReducedSchedule;

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsLeavePeriodIntermittent.title")}
      onSave={handleSave}
    >
      {claim.isMedicalLeave && (
        <Alert state="info">
          {t("pages.claimsLeavePeriodIntermittent.medicalAlert")}
        </Alert>
      )}

      <InputChoiceGroup
        {...getFunctionalInputProps("has_intermittent_leave_periods")}
        choices={[
          {
            checked: formState.has_intermittent_leave_periods === true,
            label: t("pages.claimsLeavePeriodIntermittent.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_intermittent_leave_periods === false,
            label: t("pages.claimsLeavePeriodIntermittent.choiceNo"),
            value: "false",
          },
        ]}
        hint={
          claim.isMedicalLeave
            ? t("pages.claimsLeavePeriodIntermittent.hasLeaveHint_medical")
            : null // could use `context` if another leave type needs hint text
        }
        label={t("pages.claimsLeavePeriodIntermittent.hasLeaveLabel")}
        type="radio"
      />

      <ConditionalContent
        visible={
          formState.has_intermittent_leave_periods && hasOtherLeavePeriodTypes
        }
      >
        <Alert state="warning">
          {t("pages.claimsLeavePeriodIntermittent.hybridLeaveWarning")}
        </Alert>
      </ConditionalContent>

      <ConditionalContent
        // TODO (CP-933): Remove the leave period
        fieldNamesClearedWhenHidden={[]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
        visible={
          formState.has_intermittent_leave_periods && !hasOtherLeavePeriodTypes
        }
      >
        <Heading level="2" size="1">
          {t("pages.claimsLeavePeriodIntermittent.datesSectionLabel")}
        </Heading>

        <Lead>
          <Trans
            i18nKey="pages.claimsLeavePeriodIntermittent.datesLead"
            tOptions={{ context: contentContext }}
          />
        </Lead>

        <InputDate
          {...getFunctionalInputProps(
            "leave_details.intermittent_leave_periods[0].start_date"
          )}
          label={t("pages.claimsLeavePeriodIntermittent.startDateLabel")}
          example={t("components.form.dateInputExample")}
          dayLabel={t("components.form.dateInputDayLabel")}
          monthLabel={t("components.form.dateInputMonthLabel")}
          yearLabel={t("components.form.dateInputYearLabel")}
          smallLabel
        />
        <InputDate
          {...getFunctionalInputProps(
            "leave_details.intermittent_leave_periods[0].end_date"
          )}
          label={t("pages.claimsLeavePeriodIntermittent.endDateLabel", {
            context: contentContext,
          })}
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

LeavePeriodIntermittent.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(Claim).isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(LeavePeriodIntermittent);
