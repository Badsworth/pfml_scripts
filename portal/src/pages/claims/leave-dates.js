import Claim from "../../models/Claim";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.leave_details.continuous_leave_periods"];

export const LeaveDates = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = (formState) =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsLeaveDates.title")}
      onSave={handleSave}
    >
      <InputDate
        name="leave_details.continuous_leave_periods[0].start_date"
        label={t("pages.claimsLeaveDates.startDateLabel")}
        hint={t("pages.claimsLeaveDates.startDateHint")}
        value={valueWithFallback(
          get(formState, "leave_details.continuous_leave_periods[0].start_date")
        )}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        onChange={handleInputChange}
      />
      <InputDate
        name="leave_details.continuous_leave_periods[0].end_date"
        label={t("pages.claimsLeaveDates.endDateLabel")}
        value={valueWithFallback(
          get(formState, "leave_details.continuous_leave_periods[0].end_date")
        )}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        onChange={handleInputChange}
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
