import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConcurrentLeave from "../../models/ConcurrentLeave";
import ConditionalContent from "../ConditionalContent";
import InputDate from "../InputDate";
import PropTypes from "prop-types";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a concurrent leave and amendment form
 * in the Leave Admin claim review page.
 */

const AmendableConcurrentLeave = ({ appErrors, concurrentLeave, onChange }) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(concurrentLeave);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );

  const amendLeave = (field, value) => {
    setAmendment({
      ...amendment,
      [field]: value,
    });
    onChange({ [field]: value });
  };

  const startDateErrMsg = appErrors.fieldErrorMessage(
    `concurrent_leave.leave_start_date`
  );
  const leaveDateErrMsg = appErrors.fieldErrorMessage(
    `concurrent_leave.leave_end_date`
  );

  return (
    <React.Fragment>
      <tr>
        <th scope="row">
          {formatDateRange(
            concurrentLeave.leave_start_date,
            concurrentLeave.leave_end_date
          )}
        </th>
        <td>
          <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
        </td>
      </tr>
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <tr>
          <td
            colSpan="3"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              onDestroy={() => {
                setIsAmendmentFormDisplayed(false);
                setAmendment(concurrentLeave);
                onChange(concurrentLeave);
              }}
              destroyButtonLabel={t("components.amendmentForm.cancel")}
            >
              <InputDate
                onChange={(e) => amendLeave("leave_start_date", e.target.value)}
                value={amendment.leave_start_date}
                label={t("components.amendmentForm.question_leaveStartDate")}
                errorMsg={startDateErrMsg}
                name="concurrent_leave.leave_start_date"
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputDate
                onChange={(e) => amendLeave("leave_end_date", e.target.value)}
                value={amendment.leave_end_date}
                label={t("components.amendmentForm.question_leaveEndDate")}
                errorMsg={leaveDateErrMsg}
                name="concurrent_leave.leave_end_date"
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
            </AmendmentForm>
          </td>
        </tr>
      </ConditionalContent>
    </React.Fragment>
  );
};

AmendableConcurrentLeave.propTypes = {
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  concurrentLeave: PropTypes.instanceOf(ConcurrentLeave).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default AmendableConcurrentLeave;
