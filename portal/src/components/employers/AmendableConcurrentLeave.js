import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConcurrentLeave from "../../models/ConcurrentLeave";
import ConditionalContent from "../ConditionalContent";
import Heading from "../Heading";
import InputDate from "../InputDate";
import PropTypes from "prop-types";
import { cloneDeep } from "lodash";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a concurrent leave and amendment form
 * in the Leave Admin claim review page.
 */

const AmendableConcurrentLeave = ({
  getFunctionalInputProps,
  isAddedByLeaveAdmin,
  originalConcurrentLeave,
  updateFields,
}) => {
  const { t } = useTranslation();
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] =
    useState(false);

  const handleCancelAmendment = () => {
    setIsAmendmentFormDisplayed(false);
    updateFields({ concurrent_leave: cloneDeep(originalConcurrentLeave) });
  };

  const handleDeleteAddition = () => {
    updateFields({ concurrent_leave: null });
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
        {formatDateRange(
          originalConcurrentLeave.leave_start_date,
          originalConcurrentLeave.leave_end_date
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
      <ConditionalContent
        visible={isAddedByLeaveAdmin || isAmendmentFormDisplayed}
      >
        <tr>
          <td
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
                {...getFunctionalInputProps(
                  "concurrent_leave.leave_start_date"
                )}
                label={t(
                  "components.employersAmendableConcurrentLeave.leaveStartDateLabel"
                )}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputDate
                {...getFunctionalInputProps("concurrent_leave.leave_end_date")}
                label={t(
                  "components.employersAmendableConcurrentLeave.leaveEndDateLabel"
                )}
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
  getFunctionalInputProps: PropTypes.func.isRequired,
  isAddedByLeaveAdmin: PropTypes.bool.isRequired,
  originalConcurrentLeave: PropTypes.instanceOf(ConcurrentLeave),
  updateFields: PropTypes.func.isRequired,
};

export default AmendableConcurrentLeave;
