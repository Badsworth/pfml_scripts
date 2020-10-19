import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConditionalContent from "../ConditionalContent";
import InputDate from "../InputDate";
import PreviousLeave from "../../models/PreviousLeave";
import PropTypes from "prop-types";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a previous leave and amendment form
 * in the Leave Admin claim review page.
 */

const AmendablePreviousLeave = ({ leavePeriod, onChange }) => {
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
    onChange({ id, [field]: value });
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
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <tr>
          <td
            colSpan="3"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              onCancel={() => {
                setIsAmendmentFormDisplayed(false);
                setAmendment(leavePeriod);
                onChange(leavePeriod);
              }}
            >
              <InputDate
                onChange={(e) =>
                  amendLeave(leavePeriod.id, "leave_start_date", e.target.value)
                }
                value={amendment.leave_start_date}
                label={t("components.amendmentForm.question_leaveStartDate")}
                name="leave-start-date-amendment"
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputDate
                onChange={(e) =>
                  amendLeave(leavePeriod.id, "leave_end_date", e.target.value)
                }
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
        </tr>
      </ConditionalContent>
    </React.Fragment>
  );
};

AmendablePreviousLeave.propTypes = {
  leavePeriod: PropTypes.instanceOf(PreviousLeave).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default AmendablePreviousLeave;
