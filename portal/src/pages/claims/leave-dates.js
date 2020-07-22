import Claim from "../../models/Claim";
import InputDate from "../../components/InputDate";
import Lead from "../../components/Lead";
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

export const fields = [
  "claim.temp.leave_details.start_date",
  "claim.temp.leave_details.end_date",
];

const LeaveDates = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = () =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage title={t("pages.claimsLeaveDates.title")} onSave={handleSave}>
      <InputDate
        name="temp.leave_details.start_date"
        label={t("pages.claimsLeaveDates.startDateLabel")}
        hint={
          <React.Fragment>
            <Lead>{t("pages.claimsLeaveDates.startDateLeadHint")}</Lead>
            <p>{t("pages.claimsLeaveDates.startDateHint")}</p>
            <p>{t("components.form.dateInputHint")}</p>
          </React.Fragment>
        }
        value={valueWithFallback(
          get(formState, "temp.leave_details.start_date")
        )}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        onChange={handleInputChange}
      />
      <InputDate
        name="temp.leave_details.end_date"
        label={t("pages.claimsLeaveDates.endDateLabel")}
        hint={
          <React.Fragment>
            <p>{t("pages.claimsLeaveDates.endDateHint")}</p>
            <p>{t("components.form.dateInputHint")}</p>
          </React.Fragment>
        }
        value={valueWithFallback(get(formState, "temp.leave_details.end_date"))}
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
