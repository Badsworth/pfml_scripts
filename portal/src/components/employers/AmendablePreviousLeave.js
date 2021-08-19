import PreviousLeave, {
  PreviousLeaveReason,
  PreviousLeaveType,
} from "../../models/PreviousLeave";
import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../ConditionalContent";
import Heading from "../Heading";
import InputChoiceGroup from "../InputChoiceGroup";
import InputDate from "../InputDate";
import PropTypes from "prop-types";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import useAutoFocusEffect from "../../hooks/useAutoFocusEffect";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a previous leave and amendment form
 * in the Leave Admin claim review page.
 */

const AmendablePreviousLeave = ({
  appErrors,
  isAddedByLeaveAdmin,
  onChange,
  onRemove,
  previousLeave,
  shouldShowV2,
}) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(previousLeave);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    isAddedByLeaveAdmin
  );
  const containerRef = React.createRef();
  useAutoFocusEffect({ containerRef, isAmendmentFormDisplayed });

  const getFieldPath = (field) =>
    `previous_leaves[${amendment.previous_leave_id}].${field}`;

  const getErrorMessage = (field) =>
    appErrors.fieldErrorMessage(getFieldPath(field));

  const getFormattedValue = (field, value) => {
    if (field === "leave_start_date" || field === "leave_end_date") {
      // happens if a user starts typing a date, then removes it
      // these fields aren't required, and sending an empty string returns an "invalid date" error
      return value === "" ? null : value;
    } else if (value === "true") {
      return true;
    } else if (value === "false") {
      return false;
    }

    return value;
  };

  const amendLeave = (field, value) => {
    const formStateField = isAddedByLeaveAdmin
      ? "addedPreviousLeaves"
      : "amendedPreviousLeaves";
    const formattedValue = getFormattedValue(field, value);
    setAmendment({
      ...amendment,
      [field]: formattedValue,
    });
    onChange(
      {
        previous_leave_id: previousLeave.previous_leave_id,
        [field]: formattedValue,
      },
      formStateField
    );
  };

  const handleCancelAmendment = () => {
    setIsAmendmentFormDisplayed(false);
    setAmendment(previousLeave);
    onChange(previousLeave, "amendedPreviousLeaves");
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

  const LeaveDetailsRow = () => (
    <tr>
      <th scope="row">
        {formatDateRange(
          previousLeave.leave_start_date,
          previousLeave.leave_end_date
        )}
      </th>
      <td>
        {t("components.employersAmendablePreviousLeave.leaveReasonValue", {
          context: findKeyByValue(
            PreviousLeaveReason,
            previousLeave.leave_reason
          ),
        })}
      </td>
      <td>
        <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
      </td>
    </tr>
  );

  return (
    <React.Fragment>
      {!isAddedByLeaveAdmin && <LeaveDetailsRow />}
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <tr ref={containerRef}>
          <td
            colSpan="2"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              className={className}
              destroyButtonLabel={t(
                "components.employersAmendablePreviousLeave.destroyButtonLabel",
                { context: addOrAmend }
              )}
              onDestroy={onDestroy}
            >
              <Heading level="4" size="3">
                {t("components.employersAmendablePreviousLeave.heading", {
                  context: addOrAmend,
                })}
              </Heading>
              <p>
                {t("components.employersAmendablePreviousLeave.subtitle", {
                  context: addOrAmend,
                })}
              </p>
              <ConditionalContent visible={shouldShowV2}>
                <InputChoiceGroup
                  name={getFieldPath("type")}
                  smallLabel
                  label={t(
                    "components.employersAmendablePreviousLeave.isForSameReasonAsLeaveReasonLabel"
                  )}
                  onChange={(e) => {
                    amendLeave("type", e.target.value);
                  }}
                  errorMsg={getErrorMessage("type")}
                  type="radio"
                  choices={[
                    {
                      checked:
                        get(amendment, "type") === PreviousLeaveType.sameReason,
                      label: t(
                        "components.employersAmendablePreviousLeave.choiceYes"
                      ),
                      value: PreviousLeaveType.sameReason,
                    },
                    {
                      checked:
                        get(amendment, "type") ===
                        PreviousLeaveType.otherReason,
                      label: t(
                        "components.employersAmendablePreviousLeave.choiceNo"
                      ),
                      value: PreviousLeaveType.otherReason,
                    },
                  ]}
                />
              </ConditionalContent>
              <ConditionalContent
                visible={
                  get(amendment, "type") === PreviousLeaveType.otherReason
                }
              >
                <InputChoiceGroup
                  name={getFieldPath("leave_reason")}
                  smallLabel
                  label={t(
                    "components.employersAmendablePreviousLeave.leaveReasonLabel"
                  )}
                  choices={[
                    {
                      label: t(
                        "components.employersAmendablePreviousLeave.leaveReasonValue_medical"
                      ),
                      hint: t(
                        "components.employersAmendablePreviousLeave.leaveReason_medical"
                      ),
                      value: PreviousLeaveReason.medical,
                      checked:
                        get(amendment, "leave_reason") ===
                        PreviousLeaveReason.medical,
                    },
                    {
                      label: t(
                        "components.employersAmendablePreviousLeave.leaveReasonValue_pregnancy"
                      ),
                      hint: t(
                        "components.employersAmendablePreviousLeave.leaveReason_medical"
                      ),
                      value: PreviousLeaveReason.pregnancy,
                      checked:
                        get(amendment, "leave_reason") ===
                        PreviousLeaveReason.pregnancy,
                    },
                    {
                      label: t(
                        "components.employersAmendablePreviousLeave.leaveReasonValue_bonding"
                      ),
                      hint: t(
                        "components.employersAmendablePreviousLeave.leaveReason_family"
                      ),
                      value: PreviousLeaveReason.bonding,
                      checked:
                        get(amendment, "leave_reason") ===
                        PreviousLeaveReason.bonding,
                    },
                    {
                      label: t(
                        "components.employersAmendablePreviousLeave.leaveReasonValue_care"
                      ),
                      hint: t(
                        "components.employersAmendablePreviousLeave.leaveReason_family"
                      ),
                      value: PreviousLeaveReason.care,
                      checked:
                        get(amendment, "leave_reason") ===
                        PreviousLeaveReason.care,
                    },
                    {
                      label: t(
                        "components.employersAmendablePreviousLeave.leaveReasonValue_activeDutyFamily"
                      ),
                      hint: t(
                        "components.employersAmendablePreviousLeave.leaveReason_family"
                      ),
                      value: PreviousLeaveReason.activeDutyFamily,
                      checked:
                        get(amendment, "leave_reason") ===
                        PreviousLeaveReason.activeDutyFamily,
                    },
                    {
                      label: t(
                        "components.employersAmendablePreviousLeave.leaveReasonValue_serviceMemberFamily"
                      ),
                      hint: t(
                        "components.employersAmendablePreviousLeave.leaveReason_family"
                      ),
                      value: PreviousLeaveReason.serviceMemberFamily,
                      checked:
                        get(amendment, "leave_reason") ===
                        PreviousLeaveReason.serviceMemberFamily,
                    },
                  ]}
                  type="radio"
                  onChange={(e) => {
                    amendLeave("leave_reason", e.target.value);
                  }}
                />
              </ConditionalContent>
              <InputDate
                onChange={(e) => amendLeave("leave_start_date", e.target.value)}
                value={amendment.leave_start_date}
                label={t(
                  "components.employersAmendablePreviousLeave.leaveStartDateLabel"
                )}
                errorMsg={getErrorMessage("leave_start_date")}
                name={getFieldPath("leave_start_date")}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputDate
                onChange={(e) => amendLeave("leave_end_date", e.target.value)}
                value={amendment.leave_end_date}
                label={t(
                  "components.employersAmendablePreviousLeave.leaveEndDateLabel"
                )}
                errorMsg={getErrorMessage("leave_end_date")}
                name={getFieldPath("leave_end_date")}
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
  isAddedByLeaveAdmin: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  previousLeave: PropTypes.instanceOf(PreviousLeave).isRequired,
  shouldShowV2: PropTypes.bool.isRequired,
};

export default AmendablePreviousLeave;
