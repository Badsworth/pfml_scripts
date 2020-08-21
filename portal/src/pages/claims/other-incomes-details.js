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
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.other_incomes"];

export const OtherIncomesDetails = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;
  // If the claim doesn't have any relevant entries, pre-populate the first one
  // so that it renders in the RepeatableFieldset below
  if (initialEntries.other_incomes.length === 0) {
    initialEntries.other_incomes = [new OtherIncome()];
  }
  const { formState, updateFields } = useFormState(initialEntries);
  const other_incomes = get(formState, "other_incomes");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const handleAddClick = () => {
    // Add a new blank entry
    const updatedEntries = other_incomes.concat([new OtherIncome()]);
    updateFields({ other_incomes: updatedEntries });
  };
  const handleRemoveClick = (entry, index) => {
    // Remove the specified entry
    const updatedEntries = [...other_incomes];
    updatedEntries.splice(index, 1);
    updateFields({ other_incomes: updatedEntries });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const render = (entry, index) => {
    return (
      <OtherIncomeCard
        entry={entry}
        index={index}
        getFunctionalInputProps={getFunctionalInputProps}
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
  const { entry, getFunctionalInputProps, index } = props;

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(`other_incomes[${index}].income_type`)}
        choices={Object.entries(OtherIncomeType).map(([key, value]) => {
          return {
            checked: entry.income_type === value,
            label: t("pages.claimsOtherIncomesDetails.typeChoiceLabel", {
              context: key,
            }),
            value,
          };
        })}
        label={t("pages.claimsOtherIncomesDetails.typeLabel")}
        type="radio"
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(
          `other_incomes[${index}].income_start_date`
        )}
        label={t("pages.claimsOtherIncomesDetails.startDateLabel")}
        hint={t("components.form.dateInputHint")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(`other_incomes[${index}].income_end_date`)}
        label={t("pages.claimsOtherIncomesDetails.endDateLabel")}
        hint={t("components.form.dateInputHint")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputText
        {...getFunctionalInputProps(
          `other_incomes[${index}].income_amount_dollars`
        )}
        label={t("pages.claimsOtherIncomesDetails.amountLabel")}
        hint={t("pages.claimsOtherIncomesDetails.amountHint")}
        mask="currency"
        optionalText={t("components.form.optional")}
        smallLabel
      />
    </React.Fragment>
  );
};

OtherIncomeCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.instanceOf(OtherIncome).isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withClaim(OtherIncomesDetails);
