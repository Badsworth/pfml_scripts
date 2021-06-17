import PreviousLeave, { PreviousLeaveReason } from "../../models/PreviousLeave";
import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../ConditionalContent";
import Heading from "../Heading";
import InputDate from "../InputDate";
import PropTypes from "prop-types";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a previous leave and amendment form
 * in the Leave Admin claim review page.
 */

const AmendablePreviousLeave = ({ appErrors, leavePeriod, onChange }) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(leavePeriod);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );

  const amendLeave = (id, field, value) => {
    setAmendment({
      ...amendment,
      [field]: value,
    });
    onChange({ previous_leave_id: id, [field]: value });
  };

  const startDateErrMsg = appErrors.fieldErrorMessage(
    `previous_leaves[${leavePeriod.previous_leave_id}].leave_start_date`
  );
  const leaveDateErrMsg = appErrors.fieldErrorMessage(
    `previous_leaves[${leavePeriod.previous_leave_id}].leave_end_date`
  );

  return (
    <React.Fragment>
      <tr>
        <th scope="row">
          {formatDateRange(
            leavePeriod.leave_start_date,
            leavePeriod.leave_end_date
          )}
        </th>
        <td>
          {t("components.employersPreviousLeaves.leaveReasonValue", {
            context: findKeyByValue(
              PreviousLeaveReason,
              leavePeriod.leave_reason
            ),
          })}
        </td>
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
                setAmendment(leavePeriod);
                onChange(leavePeriod);
              }}
              destroyButtonLabel={t("components.amendmentForm.cancel")}
            >
              <Heading level="4">
                {t("components.employersPreviousLeaves.leaveReasonValue", {
                  context: findKeyByValue(
                    PreviousLeaveReason,
                    leavePeriod.leave_reason
                  ),
                })}
              </Heading>
              <InputDate
                onChange={(e) =>
                  amendLeave(
                    leavePeriod.previous_leave_id,
                    "leave_start_date",
                    e.target.value
                  )
                }
                value={amendment.leave_start_date}
                label={t("components.amendmentForm.question_leaveStartDate")}
                errorMsg={startDateErrMsg}
                name={`previous_leaves[${leavePeriod.previous_leave_id}].leave_start_date`}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputDate
                onChange={(e) =>
                  amendLeave(
                    leavePeriod.previous_leave_id,
                    "leave_end_date",
                    e.target.value
                  )
                }
                value={amendment.leave_end_date}
                label={t("components.amendmentForm.question_leaveEndDate")}
                errorMsg={leaveDateErrMsg}
                name={`previous_leaves[${leavePeriod.previous_leave_id}].leave_end_date`}
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

AmendablePreviousLeave.propTypes = {
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  leavePeriod: PropTypes.instanceOf(PreviousLeave).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default AmendablePreviousLeave;
