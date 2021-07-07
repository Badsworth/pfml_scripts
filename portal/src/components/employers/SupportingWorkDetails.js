import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConditionalContent from "../ConditionalContent";
import InputNumber from "../InputNumber";
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
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );

  // TODO make sure this updates the value in the form as well.
  // TOOD jsdoc
  const handleCancel = () => {
    props.updateFields({
      hours_worked_per_week: props.initialHoursWorkedPerWeek,
    });
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
        <p className="margin-top-0">{props.initialHoursWorkedPerWeek}</p>
        <ConditionalContent visible={isAmendmentFormDisplayed}>
          <AmendmentForm
            onDestroy={() => {
              handleCancel();
              setIsAmendmentFormDisplayed(false);
            }}
            destroyButtonLabel={t("components.amendmentForm.cancel")}
            className="input-text-first-child"
          >
            <InputNumber
              {...props.getFunctionalInputProps("hours_worked_per_week")}
              label={t("components.amendmentForm.question_leavePeriodDuration")}
              hint={t(
                "components.amendmentForm.question_leavePeriodDuration_hint"
              )}
              mask="hours"
              width="small"
              smallLabel
              valueType="integer"
            />
          </AmendmentForm>
        </ConditionalContent>
      </ReviewRow>
    </React.Fragment>
  );
};

SupportingWorkDetails.propTypes = {
  getFunctionalInputProps: PropTypes.func.isRequired,
  initialHoursWorkedPerWeek: PropTypes.number.isRequired,
  updateFields: PropTypes.func.isRequired,
};

export default SupportingWorkDetails;
