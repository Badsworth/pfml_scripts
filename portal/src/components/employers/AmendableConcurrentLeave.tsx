import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConcurrentLeave from "../../models/ConcurrentLeave";
import ConditionalContent from "../ConditionalContent";
import Heading from "../Heading";
import InputDate from "../InputDate";
import PropTypes from "prop-types";
import formatDateRange from "../../utils/formatDateRange";
import useAutoFocusEffect from "../../hooks/useAutoFocusEffect";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a concurrent leave and amendment form
 * in the Leave Admin claim review page.
 */

const AmendableConcurrentLeave = ({
  appErrors,
  concurrentLeave,
  isAddedByLeaveAdmin,
  onChange,
  onRemove,
}) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(concurrentLeave);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] =
    useState(isAddedByLeaveAdmin);
  const containerRef = React.createRef();
  useAutoFocusEffect({ containerRef, isAmendmentFormDisplayed });

  const getFormattedValue = (field, value) => {
    if (field === "leave_start_date" || field === "leave_end_date") {
      // happens if a user starts typing a date, then removes it
      // these fields aren't required, and sending an empty string returns an "invalid date" error
      return value === "" ? null : value;
    }

    return value;
  };

  const amendLeave = (field, value) => {
    const formStateField = isAddedByLeaveAdmin
      ? "addedConcurrentLeave"
      : "amendedConcurrentLeave";
    const formattedValue = getFormattedValue(field, value);
    setAmendment({
      ...amendment,
      [field]: value,
    });
    onChange({ [field]: formattedValue }, formStateField);
  };

  const startDateErrMsg = appErrors.fieldErrorMessage(
    `concurrent_leave.leave_start_date`
  );
  const leaveDateErrMsg = appErrors.fieldErrorMessage(
    `concurrent_leave.leave_end_date`
  );

  const handleCancelAmendment = () => {
    setIsAmendmentFormDisplayed(false);
    setAmendment(concurrentLeave);
    onChange(concurrentLeave);
  };

  const handleDeleteAddition = () => {
    onRemove(amendment);
  };

  const addOrAmend = isAddedByLeaveAdmin ? "add" : "amend";

  const additionFormClasses = "bg-white";
  const amendmentFormClasses = "bg-base-lightest border-base-lighter";
  const className = isAddedByLeaveAdmin
    ? additionFormClasses
    : amendmentFormClasses;

  const onDestroy = isAddedByLeaveAdmin
    ? handleDeleteAddition
    : handleCancelAmendment;

  const ConcurrentLeaveDetailsRow = () => (
    <tr>
      <th scope="row">
        {/* @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2. */}
        {formatDateRange(
          concurrentLeave.leave_start_date,
          concurrentLeave.leave_end_date
        )}
      </th>
      <td>
        <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
      </td>
    </tr>
  );

  return (
    <React.Fragment>
      {!isAddedByLeaveAdmin && <ConcurrentLeaveDetailsRow />}
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        {/* @ts-expect-error ts-migrate(2322) FIXME: Type 'RefObject<unknown>' is not assignable to typ... Remove this comment to see the full error message */}
        <tr ref={containerRef}>
          <td
            // @ts-expect-error ts-migrate(2322) FIXME: Type 'string' is not assignable to type 'number'.
            colSpan="3"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              className={className}
              onDestroy={onDestroy}
              destroyButtonLabel={t(
                "components.employersAmendableConcurrentLeave.destroyButtonLabel",
                { context: addOrAmend }
              )}
            >
              <Heading level="4" size="3">
                {t("components.employersAmendableConcurrentLeave.heading", {
                  context: addOrAmend,
                })}
              </Heading>
              <p>
                {t("components.employersAmendableConcurrentLeave.subtitle", {
                  context: addOrAmend,
                })}
              </p>
              <InputDate
                onChange={(e) => amendLeave("leave_start_date", e.target.value)}
                value={amendment.leave_start_date}
                label={t(
                  "components.employersAmendableConcurrentLeave.leaveStartDateLabel"
                )}
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
                label={t(
                  "components.employersAmendableConcurrentLeave.leaveEndDateLabel"
                )}
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
  isAddedByLeaveAdmin: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
};

export default AmendableConcurrentLeave;
