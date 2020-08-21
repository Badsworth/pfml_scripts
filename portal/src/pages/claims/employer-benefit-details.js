import EmployerBenefit, {
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import Claim from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import get from "lodash/get";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.employer_benefits"];

const EmployerBenefitDetails = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;
  // If the claim doesn't have any employer benefits pre-populate the first one so that
  // it renders in the RepeatableFieldset below
  if (initialEntries.employer_benefits.length === 0) {
    initialEntries.employer_benefits = [new EmployerBenefit()];
  }
  const { formState, updateFields } = useFormState(initialEntries);
  const employer_benefits = get(formState, "employer_benefits");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const handleAddClick = () => {
    // Add a new blank entry
    const updatedEntries = employer_benefits.concat([new EmployerBenefit()]);
    updateFields({ employer_benefits: updatedEntries });
  };
  const handleRemoveClick = (entry, index) => {
    // Remove the specified benefit
    const updatedEntries = [...employer_benefits];
    updatedEntries.splice(index, 1);
    updateFields({ employer_benefits: updatedEntries });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const render = (entry, index) => {
    return (
      <EmployerBenefitCard
        entry={entry}
        getFunctionalInputProps={getFunctionalInputProps}
        index={index}
      />
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsEmployerBenefitDetails.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsEmployerBenefitDetails.sectionLabel")}
      </Heading>
      <RepeatableFieldset
        addButtonLabel={t("pages.claimsEmployerBenefitDetails.addButton")}
        entries={employer_benefits}
        headingPrefix={t(
          "pages.claimsEmployerBenefitDetails.cardHeadingPrefix"
        )}
        onAddClick={handleAddClick}
        onRemoveClick={handleRemoveClick}
        removeButtonLabel={t("pages.claimsEmployerBenefitDetails.removeButton")}
        render={render}
      />
    </QuestionPage>
  );
};

EmployerBenefitDetails.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

/**
 * Helper component for rendering employer benefit cards
 */
export const EmployerBenefitCard = (props) => {
  const { t } = useTranslation();
  const { entry, getFunctionalInputProps, index } = props;
  const selectedType = entry.benefit_type;
  // TODO: make sure that the amount gets removed if the input text is hidden
  const showAmountInputText = [
    EmployerBenefitType.shortTermDisability,
    EmployerBenefitType.permanentDisability,
    EmployerBenefitType.familyOrMedicalLeave,
  ].includes(selectedType);
  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(`employer_benefits[${index}].benefit_type`)}
        choices={Object.entries(EmployerBenefitType).map(([key, value]) => {
          return {
            checked: selectedType === value,
            label: t("pages.claimsEmployerBenefitDetails.choiceLabel", {
              context: key,
            }),
            hint: t("pages.claimsEmployerBenefitDetails.choiceHint", {
              context: key,
            }),
            value,
          };
        })}
        label={t("pages.claimsEmployerBenefitDetails.typeLabel")}
        type="radio"
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(
          `employer_benefits[${index}].benefit_start_date`
        )}
        label={t("pages.claimsEmployerBenefitDetails.startDateLabel")}
        hint={t("components.form.dateInputHint")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(
          `employer_benefits[${index}].benefit_end_date`
        )}
        label={t("pages.claimsEmployerBenefitDetails.endDateLabel")}
        hint={t("components.form.dateInputHint")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <ConditionalContent visible={showAmountInputText}>
        <InputText
          {...getFunctionalInputProps(
            `employer_benefits[${index}].benefit_amount_dollars`
          )}
          label={t("pages.claimsEmployerBenefitDetails.amountLabel")}
          hint={t("pages.claimsEmployerBenefitDetails.amountHint")}
          mask="currency"
          optionalText={t("components.form.optional")}
          smallLabel
        />
      </ConditionalContent>
    </React.Fragment>
  );
};

EmployerBenefitCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.instanceOf(EmployerBenefit).isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withClaim(EmployerBenefitDetails);
