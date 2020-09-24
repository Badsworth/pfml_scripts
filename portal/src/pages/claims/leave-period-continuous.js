import Claim, { LeaveReason } from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.temp.has_continuous_leave_periods",
  "claim.leave_details.continuous_leave_periods[0].end_date",
  "claim.leave_details.continuous_leave_periods[0].start_date",
  "claim.leave_details.continuous_leave_periods[0].leave_period_id",
];

export const LeavePeriodContinuous = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, removeField } = useFormState(
    pick(props, fields).claim
  );

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
      title={t("pages.claimsLeavePeriodContinuous.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("temp.has_continuous_leave_periods")}
        choices={[
          {
            checked: formState.temp.has_continuous_leave_periods === true,
            label: t("pages.claimsLeavePeriodContinuous.choiceYes"),
            value: "true",
          },
          {
            checked: formState.temp.has_continuous_leave_periods === false,
            label: t("pages.claimsLeavePeriodContinuous.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsLeavePeriodContinuous.hasLeaveLabel")}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "claim.leave_details.continuous_leave_periods[0]",
        ]}
        getField={getField}
        removeField={removeField}
        updateFields={updateFields}
        visible={formState.temp.has_continuous_leave_periods}
      >
        <Heading level="2" size="1">
          {t("pages.claimsLeavePeriodContinuous.datesSectionLabel")}
        </Heading>

        <Lead>
          {t("pages.claimsLeavePeriodContinuous.datesLead", {
            context: contentContext,
          })}
        </Lead>

        <InputDate
          {...getFunctionalInputProps(
            "leave_details.continuous_leave_periods[0].start_date"
          )}
          label={t("pages.claimsLeavePeriodContinuous.startDateLabel")}
          example={t("components.form.dateInputExample")}
          dayLabel={t("components.form.dateInputDayLabel")}
          monthLabel={t("components.form.dateInputMonthLabel")}
          yearLabel={t("components.form.dateInputYearLabel")}
          smallLabel
        />
        <InputDate
          {...getFunctionalInputProps(
            "leave_details.continuous_leave_periods[0].end_date"
          )}
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
  claim: PropTypes.instanceOf(Claim).isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(LeavePeriodContinuous);
