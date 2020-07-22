import EmployerBenefit, {
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import Claim from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import FormLabel from "../../components/FormLabel";
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
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.employer_benefits"];

const EmployerBenefitDetails = (props) => {
  const { t } = useTranslation();
  const initialBenefits = pick(props, fields).claim;
  // If the claim doesn't have any employer benefits pre-populate the first one so that
  // it renders in the RepeatableFieldset below
  if (initialBenefits.employer_benefits.length === 0) {
    initialBenefits.employer_benefits = [new EmployerBenefit()];
  }
  const { formState, updateFields } = useFormState(initialBenefits);
  const employer_benefits = get(formState, "employer_benefits");

  const handleSave = () => {
    return props.appLogic.updateClaim(props.claim.application_id, formState);
  };

  const handleAddClick = () => {
    // Add a new blank benefit
    const updatedBenefits = employer_benefits.concat([new EmployerBenefit()]);
    updateFields({ employer_benefits: updatedBenefits });
  };

  const handleInputChange = useHandleInputChange(updateFields);

  const handleRemoveClick = (entry, index) => {
    // Remove the specified benefit
    const updatedBenefits = [...employer_benefits];
    updatedBenefits.splice(index, 1);
    updateFields({ employer_benefits: updatedBenefits });
  };

  const render = (benefit, index) => {
    return (
      <EmployerBenefitCard
        benefit={benefit}
        index={index}
        onInputChange={handleInputChange}
      />
    );
  };

  // todo: CP-563 fix spacing issue between section label and repeatablefieldset
  return (
    <QuestionPage
      title={t("pages.claimsEmployerBenefitDetails.title")}
      onSave={handleSave}
    >
      <FormLabel component="legend">
        {t("pages.claimsEmployerBenefitDetails.sectionLabel")}
      </FormLabel>
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
const EmployerBenefitCard = (props) => {
  const { t } = useTranslation();
  const { benefit, onInputChange, index } = props;
  const selectedType = benefit.benefit_type;
  // TODO: make sure that the amount gets removed if the input text is hidden
  const showAmountInputText = [
    EmployerBenefitType.shortTermDisability,
    EmployerBenefitType.permanentDisability,
    EmployerBenefitType.familyOrMedicalLeave,
  ].includes(EmployerBenefitType[selectedType]);
  return (
    <React.Fragment>
      <InputChoiceGroup
        choices={Object.keys(EmployerBenefitType).map((type) => {
          return {
            checked: selectedType === type,
            label: t("pages.claimsEmployerBenefitDetails.choiceLabel", {
              context: type,
            }),
            hint: t("pages.claimsEmployerBenefitDetails.choiceHint", {
              context: type,
            }),
            value: type,
          };
        })}
        label={t("pages.claimsEmployerBenefitDetails.typeLabel")}
        name={`employer_benefits[${index}].benefit_type`}
        onChange={onInputChange}
        type="radio"
        smallLabel
      />
      <InputDate
        label={t("pages.claimsEmployerBenefitDetails.startDateLabel")}
        hint={t("components.form.dateInputHint")}
        name={`employer_benefits[${index}].benefit_start_date`}
        onChange={onInputChange}
        value={valueWithFallback(benefit.benefit_start_date)}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputDate
        label={t("pages.claimsEmployerBenefitDetails.endDateLabel")}
        hint={t("components.form.dateInputHint")}
        name={`employer_benefits[${index}].benefit_end_date`}
        onChange={onInputChange}
        value={valueWithFallback(benefit.benefit_end_date)}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <ConditionalContent visible={showAmountInputText}>
        <InputText
          label={t("pages.claimsEmployerBenefitDetails.amountLabel")}
          hint={t("pages.claimsEmployerBenefitDetails.amountHint")}
          name={`employer_benefits[${index}].benefit_amount`}
          onChange={onInputChange}
          optionalText={t("components.form.optionalText")}
          value={valueWithFallback(benefit.benefit_amount)}
          smallLabel
        />
      </ConditionalContent>
    </React.Fragment>
  );
};

EmployerBenefitCard.propTypes = {
  index: PropTypes.number.isRequired,
  benefit: PropTypes.instanceOf(EmployerBenefit).isRequired,
  onInputChange: PropTypes.func.isRequired,
};

export default withClaim(EmployerBenefitDetails);
