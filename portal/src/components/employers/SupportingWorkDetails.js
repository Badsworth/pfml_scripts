import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
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
  const { hoursWorkedPerWeek, onChange } = props;
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
        {t("pages.employersClaimsReview.supportingWorkDetails.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t(
          "pages.employersClaimsReview.supportingWorkDetails.hoursWorkedLabel"
        )}
        action={
          <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
        }
      >
        <p className="margin-top-0">{hoursWorkedPerWeek}</p>
        <ConditionalContent visible={isAmendmentFormDisplayed}>
          <AmendmentForm
            onCancel={() => {
              setIsAmendmentFormDisplayed(false);
              setAmendment(hoursWorkedPerWeek);
              onChange(hoursWorkedPerWeek);
            }}
            className="input-text-first-child"
          >
            <InputText
              onChange={(e) => amendDuration(e.target.value)}
              value={amendment}
              label={t("components.amendmentForm.question_leavePeriodDuration")}
              hint={t(
                "components.amendmentForm.question_leavePeriodDuration_hint"
              )}
              mask="hours"
              name="supporting-work-detail-amendment"
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
  hoursWorkedPerWeek: PropTypes.number.isRequired,
  onChange: PropTypes.func,
};

export default SupportingWorkDetails;
