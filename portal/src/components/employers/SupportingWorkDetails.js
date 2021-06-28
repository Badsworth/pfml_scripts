import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../ConditionalContent";
import InputText from "../InputText";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { useTranslation } from "../../locales/i18n";

/**
 * Display weekly hours worked for intermittent leave
 * in the Leave Admin claim review page.
 */

const SupportingWorkDetails = (props) => {
  const { t } = useTranslation();
  const { appErrors, hoursWorkedPerWeek, onChange } = props;
  const errorMsg = appErrors.fieldErrorMessage("hours_worked_per_week");
  const [amendment, setAmendment] = useState(hoursWorkedPerWeek);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );
  const amendDuration = (value) => {
    // Same logic as AmendableEmployerBenefit
    // Invalid input will default to 0, validation error message is upcoming
    const isInvalid = value === "0" || !parseFloat(value);
    const displayValue = isInvalid ? 0 : value;
    const formattedValue = isInvalid ? 0 : parseFloat(value.replace(/,/g, ""));
    setAmendment(displayValue);
    onChange(formattedValue);
  };

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersSupportingWorkDetails.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t(
          "components.employersSupportingWorkDetails.weeklyHoursWorkedLabel"
        )}
        action={
          <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
        }
      >
        <p className="margin-top-0">{hoursWorkedPerWeek}</p>
        <ConditionalContent visible={isAmendmentFormDisplayed}>
          <AmendmentForm
            onDestroy={() => {
              setIsAmendmentFormDisplayed(false);
              setAmendment(hoursWorkedPerWeek);
              onChange(hoursWorkedPerWeek);
            }}
            destroyButtonLabel={t("components.amendmentForm.cancel")}
            className="input-text-first-child"
          >
            <InputText
              onChange={(e) => amendDuration(e.target.value)}
              value={amendment}
              label={t("components.amendmentForm.question_leavePeriodDuration")}
              hint={t(
                "components.amendmentForm.question_leavePeriodDuration_hint"
              )}
              errorMsg={errorMsg}
              mask="hours"
              name="hours_worked_per_week"
              width="small"
              smallLabel
            />
          </AmendmentForm>
        </ConditionalContent>
      </ReviewRow>
    </React.Fragment>
  );
};

SupportingWorkDetails.propTypes = {
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  hoursWorkedPerWeek: PropTypes.number.isRequired,
  onChange: PropTypes.func,
};

export default SupportingWorkDetails;
