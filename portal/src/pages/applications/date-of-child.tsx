import { get, pick, set } from "lodash";
import { DateTime } from "luxon";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { ReasonQualifier } from "../../models/BenefitsApplication";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

const reasonQualifierField = "leave_details.reason_qualifier";
const childBirthDateField = "leave_details.child_birth_date";
const childPlacementDateField = "leave_details.child_placement_date";
const hasFutureChildDateField = "leave_details.has_future_child_date";
export const fields = [
  `claim.${childBirthDateField}`,
  `claim.${childPlacementDateField}`,
  `claim.${hasFutureChildDateField}`,
];

export const DateOfChild = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, getField, updateFields } = useFormState(
    pick(props, fields).claim
  );

  const reason_qualifier = get(claim, reasonQualifierField);
  const dateFieldName =
    reason_qualifier === ReasonQualifier.newBorn
      ? childBirthDateField
      : childPlacementDateField;
  const contentContext = {
    [ReasonQualifier.newBorn]: "newborn",
    [ReasonQualifier.adoption]: "adopt_foster",
    [ReasonQualifier.fosterCare]: "adopt_foster",
  };

  const handleSave = () => {
    // Assumes that the birth/placement date is in the same timezone as the user's browser
    const now = DateTime.local().toISODate();
    // Compare the two dates lexicographically. This works since they're both in
    // ISO-8601 format, eg "2020-10-13"
    const isFutureChildDate = getField(dateFieldName) > now;
    set(formState, hasFutureChildDateField, isFutureChildDate);

    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsBondingDateOfChild.title")}
      onSave={handleSave}
    >
      <InputDate
        {...getFunctionalInputProps(dateFieldName)}
        label={t("pages.claimsBondingDateOfChild.sectionLabel", {
          context: contentContext[reason_qualifier],
        })}
        example={t("components.form.dateInputExample")}
        hint={
          reason_qualifier === ReasonQualifier.newBorn
            ? t("pages.claimsBondingDateOfChild.birthHint")
            : null
        }
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
    </QuestionPage>
  );
};

DateOfChild.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withBenefitsApplication(DateOfChild);
