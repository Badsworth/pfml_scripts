import Claim from "../../models/Claim";
import ClaimsApi from "../../api/ClaimsApi";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import routeWithParams from "../../utils/routeWithParams";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import useHandleSave from "../../hooks/useHandleSave";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const LeaveDates = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(props.claim);
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = useHandleSave(
    (formState) => props.claimsApi.updateClaim(new Claim(formState)),
    (result) => props.updateClaim(result.claim)
  );

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsLeaveDates.title")}
      onSave={handleSave}
      nextPage={routeWithParams("claims.duration", props.query)}
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
  updateClaim: PropTypes.func,
  claimsApi: PropTypes.instanceOf(ClaimsApi),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(LeaveDates);
