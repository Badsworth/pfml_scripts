import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../models/OtherIncome";
import { cloneDeep, get, isFinite, isNil, pick } from "lodash";
import Claim from "../../models/Claim";
import Dropdown from "../../components/Dropdown";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import InputText from "../../components/InputText";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.other_incomes",
  "claim.other_incomes[*].income_amount_dollars",
  "claim.other_incomes[*].income_amount_frequency",
  "claim.other_incomes[*].income_end_date",
  "claim.other_incomes[*].income_start_date",
  "claim.other_incomes[*].income_type",
];

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

  const handleSave = async () => {
    // Make sure income_amount_dollars is a number.
    // TODO (CP-1528): Refactor Currency Masking
    // There's a similar function in EmployerBenefitDetails.
    const patchData = cloneDeep(formState);
    patchData.other_incomes = patchData.other_incomes.map((income) => {
      const val = income.income_amount_dollars;
      const number =
        isFinite(val) || isNil(val) ? val : Number(val.replace(/,/g, ""));
      return { ...income, income_amount_dollars: number };
    });
    await appLogic.claims.update(claim.application_id, patchData);
  };

  const handleAddClick = () => {
    // Add a new blank entry
    const updatedEntries = other_incomes.concat([new OtherIncome()]);
    updateFields({ other_incomes: updatedEntries });
  };

  const otherLeaves = appLogic.otherLeaves;
  const handleRemoveClick = async (entry, index) => {
    let entrySavedToApi = !!entry.other_income_id;
    if (entrySavedToApi) {
      // Try to delete the entry from the API
      const success = await otherLeaves.removeOtherIncome(
        claim.application_id,
        entry.other_income_id
      );
      entrySavedToApi = !success;
    }

    if (!entrySavedToApi) {
      const updatedEntries = [...other_incomes];
      updatedEntries.splice(index, 1);
      updateFields({ other_incomes: updatedEntries });
    }
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

      <LeaveDatesAlert
        startDate={claim.leaveStartDate}
        endDate={claim.leaveEndDate}
        headingLevel="3"
      />

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

  const incomeFrequencyChoices = Object.entries(OtherIncomeFrequency).map(
    ([frequencyKey, frequency]) => {
      return {
        label: t("pages.claimsOtherIncomesDetails.amountFrequency", {
          context: frequencyKey,
        }),
        value: frequency,
      };
    }
  );

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(`other_incomes[${index}].income_type`)}
        choices={[
          "workersCompensation",
          "unemployment",
          "ssdi",
          "retirementDisability",
          "jonesAct",
          "railroadRetirement",
          "otherEmployer",
        ].map((otherIncomeTypeKey) => {
          return {
            checked: entry.income_type === OtherIncomeType[otherIncomeTypeKey],
            label: t("pages.claimsOtherIncomesDetails.typeChoiceLabel", {
              context: otherIncomeTypeKey,
            }),
            value: OtherIncomeType[otherIncomeTypeKey],
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
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(`other_incomes[${index}].income_end_date`)}
        label={t("pages.claimsOtherIncomesDetails.endDateLabel")}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <Fieldset>
        <FormLabel
          component="legend"
          small
          optionalText={t("components.form.optional")}
        >
          {t("pages.claimsOtherIncomesDetails.amountLegend")}
        </FormLabel>
        <InputText
          {...getFunctionalInputProps(
            `other_incomes[${index}].income_amount_dollars`
          )}
          inputMode="numeric"
          label={t("pages.claimsOtherIncomesDetails.amountLabel")}
          labelClassName="text-normal margin-top-0"
          formGroupClassName="margin-top-05"
          mask="currency"
          width="medium"
          smallLabel
        />
        <Dropdown
          {...getFunctionalInputProps(
            `other_incomes[${index}].income_amount_frequency`
          )}
          choices={incomeFrequencyChoices}
          label={t("pages.claimsOtherIncomesDetails.amountFrequencyLabel")}
          labelClassName="text-normal margin-top-0"
          formGroupClassName="margin-top-1"
          smallLabel
        />
      </Fieldset>
    </React.Fragment>
  );
};

OtherIncomeCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.object.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withClaim(OtherIncomesDetails);
