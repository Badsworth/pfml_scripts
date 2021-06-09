import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../models/OtherIncome";
import React, { useEffect, useRef } from "react";
import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import Dropdown from "../../components/Dropdown";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputCurrency from "../../components/InputCurrency";
import InputDate from "../../components/InputDate";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

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
  const limit = 6;

  const initialEntries = pick(props, fields).claim;
  const useInitialEntries = useRef(true);
  // If the claim doesn't have any relevant entries, pre-populate the first one
  // so that it renders in the RepeatableFieldset below
  if (initialEntries.other_incomes.length === 0) {
    initialEntries.other_incomes = [new OtherIncome()];
  }
  const { formState, updateFields } = useFormState(initialEntries);
  const other_incomes = get(formState, "other_incomes");

  useEffect(() => {
    // Don't bother calling updateFields() when the page first renders
    if (useInitialEntries.current) {
      useInitialEntries.current = false;
      return;
    }

    // When there's a validation error, we get back the list of other_incomes with other_income_ids from the API
    // When claim.other_leaves updates, we also need to update the formState values to include the other_income_ids,
    // so on subsequent submits, we don't create new other_income records
    updateFields({ other_incomes: claim.other_incomes });
  }, [claim.other_incomes, updateFields]);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

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
        limit={limit}
        limitMessage={t("pages.claimsOtherIncomesDetails.limitMessage", {
          limit,
        })}
      />
    </QuestionPage>
  );
};

OtherIncomesDetails.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
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

OtherIncomeCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.object.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withBenefitsApplication(OtherIncomesDetails);
