import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../models/OtherIncome";
import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Dropdown from "../../components/core/Dropdown";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import Heading from "../../components/core/Heading";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputCurrency from "../../components/core/InputCurrency";
import InputDate from "../../components/core/InputDate";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/core/RepeatableFieldset";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";

export const fields = [
  "claim.other_incomes",
  "claim.other_incomes[*].income_amount_dollars",
  "claim.other_incomes[*].income_amount_frequency",
  "claim.other_incomes[*].income_end_date",
  "claim.other_incomes[*].income_start_date",
  "claim.other_incomes[*].income_type",
];

export const OtherIncomesDetails = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const limit = 6;

  const initialEntries = pick(props, fields).claim || { other_incomes: [] };
  // If the claim doesn't have any relevant entries, pre-populate the first one
  // so that it renders in the RepeatableFieldset below
  if (initialEntries.other_incomes.length === 0) {
    initialEntries.other_incomes = [new OtherIncome()];
  }

  const { formState, updateFields } = useFormState(initialEntries);
  const other_incomes = get(formState, "other_incomes");

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const handleAddClick = () => {
    // Add a new blank entry
    const updatedEntries = other_incomes.concat([new OtherIncome()]);
    updateFields({ other_incomes: updatedEntries });
  };

  const handleRemoveClick = (entry: OtherIncome, index: number) => {
    const updatedIncomes = [...other_incomes];
    updatedIncomes.splice(index, 1);
    updateFields({ other_incomes: updatedIncomes });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const render = (entry: OtherIncome, index: number) => {
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
        limit={limit}
        limitMessage={t("pages.claimsOtherIncomesDetails.limitMessage", {
          limit,
        })}
      />
    </QuestionPage>
  );
};

interface OtherIncomeCardProps {
  index: number;
  entry: OtherIncome;
  getFunctionalInputProps: ReturnType<typeof useFunctionalInputProps>;
}

/**
 * Group of fields for an OtherIncome instance
 */
export const OtherIncomeCard = (props: OtherIncomeCardProps) => {
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

  const choiceKeys: Array<keyof typeof OtherIncomeType> = [
    "workersCompensation",
    "unemployment",
    "ssdi",
    "retirementDisability",
    "jonesAct",
    "railroadRetirement",
    "otherEmployer",
  ];

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(`other_incomes[${index}].income_type`)}
        choices={choiceKeys.map((otherIncomeTypeKey) => {
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
        <FormLabel component="legend" small>
          {t("pages.claimsOtherIncomesDetails.amountLegend")}
        </FormLabel>
        <InputCurrency
          {...getFunctionalInputProps(
            `other_incomes[${index}].income_amount_dollars`,
            { fallbackValue: null }
          )}
          label={t("pages.claimsOtherIncomesDetails.amountLabel")}
          labelClassName="text-normal margin-top-0"
          formGroupClassName="margin-top-05"
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

export default withBenefitsApplication(OtherIncomesDetails);
