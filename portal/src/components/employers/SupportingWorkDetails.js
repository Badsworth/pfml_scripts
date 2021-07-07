import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConditionalContent from "../ConditionalContent";
import InputNumber from "../InputNumber";
import Heading from "../Heading";
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
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] =
    useState(false);

  /**
   * Cancels an amendment to hours_worked_per_week by restoring the initial value.
   */
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
            className="bg-base-lightest border-base-lighter"
          >
            <Heading level="4" size="3">
              {t("components.employersSupportingWorkDetails.heading_amend")}
            </Heading>
            <p>
              {t("components.employersSupportingWorkDetails.subtitle_amend")}
            </p>
            <InputNumber
              {...props.getFunctionalInputProps("hours_worked_per_week")}
              label={t(
                "components.employersSupportingWorkDetails.leavePeriodDurationLabel"
              )}
              hint={t(
                "components.employersSupportingWorkDetails.leavePeriodDurationHint"
              )}
              mask="hours"
              width="small"
              smallLabel
              valueType="float"
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
