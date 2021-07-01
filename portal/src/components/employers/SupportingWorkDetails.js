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
import InputNumber from "../InputNumber";

/**
 * Display weekly hours worked for intermittent leave
 * in the Leave Admin claim review page.
 */

const SupportingWorkDetails = (props) => {
  const { t } = useTranslation();
  const { getFunctionalInputProps, hoursWorkedPerWeek } = props;
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );

  const functionalInputProps = {
    ...getFunctionalInputProps("hours_worked_per_week"),
  };

  const handleCancel = (e) => {
    console.log("figure me out");
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
              // TODO rename/refactor bc it's ugly
              functionalInputProps.onChange(hoursWorkedPerWeek);
              setIsAmendmentFormDisplayed(false);
            }}
            destroyButtonLabel={t("components.amendmentForm.cancel")}
            className="input-text-first-child"
          >
            <InputNumber
              {...functionalInputProps}
              // onChange={(e) => amendDuration(e.target.value)}
              // value={amendment}
              label={t("components.amendmentForm.question_leavePeriodDuration")}
              hint={t(
                "components.amendmentForm.question_leavePeriodDuration_hint"
              )}
              // errorMsg={errorMsg}
              // TODO do we need this?
              mask="hours"
              // name="hours_worked_per_week"
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
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
  hoursWorkedPerWeek: PropTypes.number.isRequired,
  onChange: PropTypes.func,
};

export default SupportingWorkDetails;
