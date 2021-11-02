import React, { useEffect, useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../ConditionalContent";
import Heading from "../Heading";
import InputNumber from "../InputNumber";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { get } from "lodash";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import usePreviousValue from "../../hooks/usePreviousValue";
import { useTranslation } from "../../locales/i18n";

interface SupportingWorkDetailsProps {
  appErrors: AppErrorInfoCollection;
  clearField: (arg: string) => void;
  getField: (arg: string) => string;
  getFunctionalInputProps: ReturnType<typeof useFunctionalInputProps>;
  initialHoursWorkedPerWeek: number | null;
  updateFields: (fields: { [fieldName: string]: unknown }) => void;
}

/**
 * Display weekly hours worked for intermittent leave
 * in the Leave Admin claim review page.
 */

const SupportingWorkDetails = (props: SupportingWorkDetailsProps) => {
  const { t } = useTranslation();
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] =
    useState(false);
  const functionalInputProps = props.getFunctionalInputProps(
    "hours_worked_per_week"
  );

  // this forces open the amendment form if an error exists for it.
  // without tracking the previous value, we run into this scenario:
  // - "errorMessage" is truthy; component opens amendment form.
  // - user clicks "Cancel amendment"; calls setIsAmendmentFormDisplayed(false).
  // - component re-renders.
  // - "errorMessage" is truthy; component opens amendment form.
  // - user cannot ever close the amendment form.
  const errorMessage = get(props, "appErrors.items[0].message");
  const amendmentFormPreviouslyDisplayed = usePreviousValue(
    isAmendmentFormDisplayed
  );
  useEffect(() => {
    if (!amendmentFormPreviouslyDisplayed) {
      setIsAmendmentFormDisplayed(!!errorMessage);
    }
    // use errorMessage instead of functionalInputProps.errorMsg because the
    // dependency list does a shallow comparison, and the latter returns objects.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [errorMessage]);

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
      </ReviewRow>
      <ConditionalContent
        getField={props.getField}
        clearField={props.clearField}
        updateFields={props.updateFields}
        fieldNamesClearedWhenHidden={["hours_worked_per_week"]}
        visible={isAmendmentFormDisplayed}
      >
        <AmendmentForm
          onDestroy={() => setIsAmendmentFormDisplayed(false)}
          destroyButtonLabel={t("components.amendmentForm.cancel")}
          className="bg-base-lightest border-base-lighter"
        >
          <Heading level="4" size="3">
            {t("components.employersSupportingWorkDetails.heading_amend")}
          </Heading>
          <p>{t("components.employersSupportingWorkDetails.subtitle_amend")}</p>
          <InputNumber
            {...functionalInputProps}
            label={t(
              "components.employersSupportingWorkDetails.leavePeriodDurationLabel"
            )}
            hint={t(
              "components.employersSupportingWorkDetails.leavePeriodDurationHint"
            )}
            mask="hours"
            width="small"
            smallLabel
            valueType="integer"
          />
        </AmendmentForm>
      </ConditionalContent>
    </React.Fragment>
  );
};

export default SupportingWorkDetails;
