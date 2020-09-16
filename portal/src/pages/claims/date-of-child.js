import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { ReasonQualifier } from "../../models/Claim";
import get from "lodash/get";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

const reasonQualifierField = "leave_details.reason_qualifier";
const childBirthDateField = "leave_details.child_birth_date";
const childPlacementDateField = "leave_details.child_placement_date";
export const fields = [
  `claim.${childBirthDateField}`,
  `claim.${childPlacementDateField}`,
];

export const DateOfChild = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);

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

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

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
          reason_qualifier === ReasonQualifier.newBorn &&
          t("pages.claimsBondingDateOfChild.birthHint")
        }
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />

      {/* {...getFunctionalInputProps(childPlacementDateField)}
          label={t("pages.claimsBondingDateOfChild.adoptionFosterSectionLabel")}
          example={t("components.form.dateInputExample")}
          dayLabel={t("components.form.dateInputDayLabel")}
          monthLabel={t("components.form.dateInputMonthLabel")}
          yearLabel={t("components.form.dateInputYearLabel")}
        /> */}
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

export default withClaim(DateOfChild);
