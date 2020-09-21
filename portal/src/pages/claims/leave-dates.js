import Claim, { LeaveReason } from "../../models/Claim";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.leave_details.continuous_leave_periods[0].end_date",
  "claim.leave_details.continuous_leave_periods[0].start_date",
];

export const LeaveDates = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = async () => {
    await appLogic.claims.update(claim.application_id, formState);
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

  // TODO (CP-984): Separately collect start and end dates for Reduced and Intermittent leaves
  return (
    <QuestionPage title={t("pages.claimsLeaveDates.title")} onSave={handleSave}>
      <InputDate
        {...getFunctionalInputProps(
          "leave_details.continuous_leave_periods[0].start_date"
        )}
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
        {...getFunctionalInputProps(
          "leave_details.continuous_leave_periods[0].end_date"
        )}
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
