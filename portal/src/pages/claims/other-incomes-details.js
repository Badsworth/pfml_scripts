import OtherIncome, { OtherIncomeType } from "../../models/OtherIncome";
import Claim from "../../models/Claim";
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
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.other_incomes"];

export const OtherIncomesDetails = (props) => {
  const { t } = useTranslation();
  const initialEntries = pick(props, fields).claim;
  // If the claim doesn't have any relevant entries, pre-populate the first one
  // so that it renders in the RepeatableFieldset below
  if (initialEntries.other_incomes.length === 0) {
    initialEntries.other_incomes = [new OtherIncome()];
  }
  const { formState, updateFields } = useFormState(initialEntries);
  const other_incomes = get(formState, "other_incomes");

  const handleSave = () => {
    return props.appLogic.updateClaim(props.claim.application_id, formState);
  };

  const handleAddClick = () => {
    // Add a new blank entry
    const updatedEntries = other_incomes.concat([new OtherIncome()]);
    updateFields({ other_incomes: updatedEntries });
  };

  const handleInputChange = useHandleInputChange(updateFields);

  const handleRemoveClick = (entry, index) => {
    // Remove the specified entry
    const updatedEntries = [...other_incomes];
    updatedEntries.splice(index, 1);
    updateFields({ other_incomes: updatedEntries });
  };

  const render = (entry, index) => {
    return (
      <OtherIncomeCard
        entry={entry}
        index={index}
        onInputChange={handleInputChange}
      />
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsOtherIncomesDetails.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsOtherIncomesDetails.sectionLabel")}
      </Heading>
      <RepeatableFieldset
        addButtonLabel={t("pages.claimsOtherIncomesDetails.addButton")}
        entries={other_incomes}
        headingPrefix={t("pages.claimsOtherIncomesDetails.cardHeadingPrefix")}
        onAddClick={handleAddClick}
        onRemoveClick={handleRemoveClick}
        removeButtonLabel={t("pages.claimsOtherIncomesDetails.removeButton")}
        render={render}
      />
    </QuestionPage>
  );
};

OtherIncomesDetails.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

/**
 * Group of fields for an OtherIncome instance
 */
export const OtherIncomeCard = (props) => {
  const { t } = useTranslation();
  const { entry, onInputChange, index } = props;

  return (
    <React.Fragment>
      <InputChoiceGroup
        choices={Object.keys(OtherIncomeType).map((type) => {
          return {
            checked: entry.income_type === type,
            label: t("pages.claimsOtherIncomesDetails.typeChoiceLabel", {
              context: type,
            }),
            value: type,
          };
        })}
        label={t("pages.claimsOtherIncomesDetails.typeLabel")}
        name={`other_incomes[${index}].income_type`}
        onChange={onInputChange}
        type="radio"
        smallLabel
      />
      <InputDate
        label={t("pages.claimsOtherIncomesDetails.startDateLabel")}
        hint={t("components.form.dateInputHint")}
        name={`other_incomes[${index}].income_start_date`}
        onChange={onInputChange}
        value={valueWithFallback(entry.income_start_date)}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputDate
        label={t("pages.claimsOtherIncomesDetails.endDateLabel")}
        hint={t("components.form.dateInputHint")}
        name={`other_incomes[${index}].income_end_date`}
        onChange={onInputChange}
        value={valueWithFallback(entry.income_end_date)}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputText
        label={t("pages.claimsOtherIncomesDetails.amountLabel")}
        hint={t("pages.claimsOtherIncomesDetails.amountHint")}
        name={`other_incomes[${index}].income_amount_dollars`}
        onChange={onInputChange}
        optionalText={t("components.form.optionalText")}
        value={valueWithFallback(entry.income_amount_dollars)}
        smallLabel
      />
    </React.Fragment>
  );
};

OtherIncomeCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.instanceOf(OtherIncome).isRequired,
  onInputChange: PropTypes.func.isRequired,
};

export default withClaim(OtherIncomesDetails);
