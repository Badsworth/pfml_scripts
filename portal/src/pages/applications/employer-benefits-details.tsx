import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import ConditionalContent from "../../components/ConditionalContent";
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
import React from "react";
import RepeatableFieldset from "../../components/RepeatableFieldset";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.employer_benefits",
  "claim.employer_benefits[*].benefit_amount_dollars",
  "claim.employer_benefits[*].benefit_amount_frequency",
  "claim.employer_benefits[*].benefit_end_date",
  "claim.employer_benefits[*].benefit_start_date",
  "claim.employer_benefits[*].benefit_type",
  "claim.employer_benefits[*].is_full_salary_continuous",
];

export const EmployerBenefitsDetails = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const limit = 6;

  const initialEntries = pick(props, fields).claim;
  // If the claim doesn't have any employer benefits pre-populate the first one so that
  // it renders in the RepeatableFieldset below
  if (initialEntries.employer_benefits.length === 0) {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    initialEntries.employer_benefits = [new EmployerBenefit()];
  }
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState(initialEntries);
  const employer_benefits = get(formState, "employer_benefits");

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const handleAddClick = () => {
    // Add a new blank entry
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    const updatedEntries = employer_benefits.concat([new EmployerBenefit()]);
    updateFields({ employer_benefits: updatedEntries });
  };

  const handleRemoveClick = (entry, index) => {
    const updatedBenefits = [...employer_benefits];
    updatedBenefits.splice(index, 1);
    updateFields({ employer_benefits: updatedBenefits });
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
        updateFields={updateFields}
      />
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsEmployerBenefitsDetails.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsEmployerBenefitsDetails.sectionLabel")}
      </Heading>

      <LeaveDatesAlert
        startDate={claim.leaveStartDate}
        endDate={claim.leaveEndDate}
        headingLevel="3"
      />

      <RepeatableFieldset
        addButtonLabel={t("pages.claimsEmployerBenefitsDetails.addButton")}
        entries={employer_benefits}
        headingPrefix={t(
          "pages.claimsEmployerBenefitsDetails.cardHeadingPrefix"
        )}
        onAddClick={handleAddClick}
        onRemoveClick={handleRemoveClick}
        removeButtonLabel={t(
          "pages.claimsEmployerBenefitsDetails.removeButton"
        )}
        render={render}
        limit={limit}
        limitMessage={t("pages.claimsEmployerBenefitsDetails.limitMessage", {
          limit,
        })}
      />
    </QuestionPage>
  );
};

EmployerBenefitsDetails.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
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
  const { entry, getFunctionalInputProps, index, updateFields } = props;
  const clearField = (fieldName) => updateFields({ [fieldName]: null });
  // Since we are not passing the formState to the benefit card,
  // get the field value from the entry by removing the field path
  const getEntryField = (fieldName) =>
    get(entry, fieldName.replace(`employer_benefits[${index}].`, ""));
  const selectedType = entry.benefit_type;

  const benefitFrequencyChoices = ["daily", "weekly", "monthly", "inTotal"].map(
    (frequencyKey) => {
      return {
        label: t("pages.claimsEmployerBenefitsDetails.amountFrequency", {
          context: frequencyKey,
        }),
        value: EmployerBenefitFrequency[frequencyKey],
      };
    }
  );

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(`employer_benefits[${index}].benefit_type`)}
        choices={[
          "shortTermDisability",
          "permanentDisability",
          "familyOrMedicalLeave",
        ].map((benefitTypeKey) => {
          return {
            checked: selectedType === EmployerBenefitType[benefitTypeKey],
            label: t("pages.claimsEmployerBenefitsDetails.choiceLabel", {
              context: benefitTypeKey,
            }),
            hint:
              benefitTypeKey !== "permanentDisability" &&
              t("pages.claimsEmployerBenefitsDetails.choiceHint", {
                context: benefitTypeKey,
              }),
            value: EmployerBenefitType[benefitTypeKey],
          };
        })}
        label={t("pages.claimsEmployerBenefitsDetails.typeLabel")}
        type="radio"
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(
          `employer_benefits[${index}].benefit_start_date`
        )}
        label={t("pages.claimsEmployerBenefitsDetails.startDateLabel")}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        smallLabel
      />
      <InputDate
        {...getFunctionalInputProps(
          `employer_benefits[${index}].benefit_end_date`
        )}
        label={t("pages.claimsEmployerBenefitsDetails.endDateLabel")}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        optionalText={t("components.form.optional")}
        smallLabel
      />
      <InputChoiceGroup
        {...getFunctionalInputProps(
          `employer_benefits[${index}].is_full_salary_continuous`
        )}
        choices={[
          {
            checked: entry.is_full_salary_continuous === true,
            label: t("pages.claimsEmployerBenefitsDetails.choiceLabel", {
              context: "yes",
            }),
            value: "true",
          },
          {
            checked: entry.is_full_salary_continuous === false,
            label: t("pages.claimsEmployerBenefitsDetails.choiceLabel", {
              context: "no",
            }),
            value: "false",
          },
        ]}
        label={t(
          "pages.claimsEmployerBenefitsDetails.isFullSalaryContinuousLabel"
        )}
        type="radio"
        smallLabel
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          `employer_benefits[${index}].benefit_amount_frequency`,
          `employer_benefits[${index}].benefit_amount_dollars`,
        ]}
        clearField={clearField}
        getField={getEntryField}
        updateFields={updateFields}
        visible={get(entry, "is_full_salary_continuous") === false}
      >
        <Fieldset>
          <FormLabel component="legend" small>
            {t("pages.claimsEmployerBenefitsDetails.amountLegend")}
          </FormLabel>
          <InputCurrency
            {...getFunctionalInputProps(
              `employer_benefits[${index}].benefit_amount_dollars`,
              { fallbackValue: null }
            )}
            label={t("pages.claimsEmployerBenefitsDetails.amountLabel")}
            labelClassName="text-normal margin-top-0"
            formGroupClassName="margin-top-05"
            smallLabel
          />
          <Dropdown
            {...getFunctionalInputProps(
              `employer_benefits[${index}].benefit_amount_frequency`
            )}
            choices={benefitFrequencyChoices}
            label={t(
              "pages.claimsEmployerBenefitsDetails.amountFrequencyLabel"
            )}
            labelClassName="text-normal margin-top-0"
            smallLabel
          />
        </Fieldset>
      </ConditionalContent>
    </React.Fragment>
  );
};

EmployerBenefitCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.object.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
  updateFields: PropTypes.func.isRequired,
};

export default withBenefitsApplication(EmployerBenefitsDetails);
