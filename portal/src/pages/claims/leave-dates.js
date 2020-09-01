import Claim, { LeaveReason } from "../../models/Claim";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import merge from "lodash/merge";
import pick from "lodash/pick";
import set from "lodash/set";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.temp.leave_details.start_date",
  "claim.temp.leave_details.end_date",
];

export const LeaveDates = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () => {
    // TODO (CP-724): Look into updating the API interface to accept a single leave_details object rather than
    // separate objects for continuous / intermittent / reduced schedule leave types.
    const leave_details = get(formState, "temp.leave_details");
    if (claim.isContinuous) {
      // merge leave period data from API with formstate data
      const leave_period = get(
        claim,
        "leave_details.continuous_leave_periods[0]"
      );
      set(
        formState,
        "leave_details.continuous_leave_periods[0]",
        merge(leave_period, leave_details)
      );
    }

    if (claim.isIntermittent) {
      // merge leave period data from API with formstate data
      const leave_period = get(
        claim,
        "leave_details.intermittent_leave_periods[0]"
      );
      set(
        formState,
        "leave_details.intermittent_leave_periods[0]",
        merge(leave_period, leave_details)
      );
    }

    if (claim.isReducedSchedule) {
      // merge leave period data from API with formstate data
      const leave_period = get(
        claim,
        "leave_details.reduced_schedule_leave_periods[0]"
      );
      set(
        formState,
        "leave_details.reduced_schedule_leave_periods[0]",
        merge(leave_period, leave_details)
      );
    }

    appLogic.claims.update(claim.application_id, formState);
  };

  const contentContext = {
    [LeaveReason.bonding]: "bonding",
    [LeaveReason.medical]: "medical",
  };
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage title={t("pages.claimsLeaveDates.title")} onSave={handleSave}>
      <InputDate
        {...getFunctionalInputProps("temp.leave_details.start_date")}
        label={t("pages.claimsLeaveDates.startDateLabel", {
          context: contentContext[claim.leave_details.reason],
        })}
        example={t("components.form.dateInputExample")}
        hint={
          <React.Fragment>
            <p>
              {t("pages.claimsLeaveDates.startDateLeadHint", {
                context: contentContext[claim.leave_details.reason],
              })}
            </p>
            <p>
              {t("pages.claimsLeaveDates.startDateHint", {
                context: contentContext[claim.leave_details.reason],
              })}
            </p>
          </React.Fragment>
        }
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
      <InputDate
        {...getFunctionalInputProps("temp.leave_details.end_date")}
        label={t("pages.claimsLeaveDates.endDateLabel", {
          context: contentContext[claim.leave_details.reason],
        })}
        example={t("components.form.dateInputExample")}
        hint={t("pages.claimsLeaveDates.endDateHint", {
          context: contentContext[claim.leave_details.reason],
        })}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
    </QuestionPage>
  );
};

LeaveDates.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(LeaveDates);
