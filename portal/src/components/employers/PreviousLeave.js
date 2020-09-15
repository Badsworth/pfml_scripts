import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import InputDate from "../InputDate";
import PropTypes from "prop-types";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a previous leave and amendment form
 * in the Leave Admin claim review page.
 */

const PreviousLeave = ({ leavePeriod }) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(leavePeriod);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );

  const amendLeave = (field, value) => {
    setAmendment({
      ...amendment,
      [field]: value,
    });
  };

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
          {t("pages.employersClaimsReview.durationBasis_days", {
            numOfDays: t("pages.employersClaimsReview.notApplicable"),
          })}
        </td>
        <td>
          <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
        </td>
      </tr>
      {isAmendmentFormDisplayed && (
        <tr>
          <td
            colSpan="2"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              onCancel={() => {
                setIsAmendmentFormDisplayed(false);
                setAmendment(leavePeriod);
              }}
            >
              <InputDate
                onChange={(e) => amendLeave("leave_start_date", e.target.value)}
                value={amendment.leave_start_date}
                label={t("components.amendmentForm.question_leaveStartDate")}
                name="leave-start-date-amendment"
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputDate
                onChange={(e) => amendLeave("leave_end_date", e.target.value)}
                value={amendment.leave_end_date}
                label={t("components.amendmentForm.question_leaveEndDate")}
                name="leave-end-date-amendment"
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
            </AmendmentForm>
          </td>
          <td colSpan="2" />
        </tr>
      )}
    </React.Fragment>
  );
};

PreviousLeave.propTypes = {
  leavePeriod: PropTypes.object.isRequired,
};

export default PreviousLeave;
