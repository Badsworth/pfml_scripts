import EmployerBenefit, {
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import ConditionalContent from "../../components/ConditionalContent";
import Fieldset from "../../components/core/Fieldset";
import Heading from "../../components/core/Heading";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputDate from "../../components/core/InputDate";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../components/core/RepeatableFieldset";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";

export const fields = [
  "claim.employer_benefits",
  "claim.employer_benefits[*].benefit_end_date",
  "claim.employer_benefits[*].benefit_start_date",
  "claim.employer_benefits[*].benefit_type",
  "claim.employer_benefits[*].is_full_salary_continuous",
];

export const EmployerBenefitsDetails = (
  props: WithBenefitsApplicationProps
) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const limit = 6;

  const initialEntries = pick(props, fields).claim || { employer_benefits: [] };
  // If the claim doesn't have any employer benefits pre-populate the first one so that
  // it renders in the RepeatableFieldset below
  if (initialEntries.employer_benefits.length === 0) {
    initialEntries.employer_benefits = [new EmployerBenefit()];
  }

  const { formState, updateFields } = useFormState(initialEntries);
  const employer_benefits: EmployerBenefit[] = get(
    formState,
    "employer_benefits"
  );

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const handleAddClick = () => {
    // Add a new blank entry
    const updatedEntries = employer_benefits.concat([new EmployerBenefit()]);
    updateFields({ employer_benefits: updatedEntries });
  };

  const handleRemoveClick = (entry: EmployerBenefit, index: number) => {
    const updatedBenefits = [...employer_benefits];
    updatedBenefits.splice(index, 1);
    updateFields({ employer_benefits: updatedBenefits });
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const render = (entry: EmployerBenefit, index: number) => {
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

interface EmployerBenefitCardProps {
  index: number;
  entry: EmployerBenefit;
  getFunctionalInputProps: ReturnType<typeof useFunctionalInputProps>;
  updateFields: (fields: { [fieldName: string]: unknown }) => void;
}

/**
 * Helper component for rendering employer benefit cards
 */
export const EmployerBenefitCard = (props: EmployerBenefitCardProps) => {
  const { t } = useTranslation();
  const { entry, getFunctionalInputProps, index, updateFields } = props;
  const clearField = (fieldName: string) => updateFields({ [fieldName]: null });

  // Since we are not passing the formState to the benefit card,
  // get the field value from the entry by removing the field path
  const getEntryField = (fieldName: string) => {
    return get(
      entry,
      fieldName.replace(`employer_benefits[${index}].`, ""),
      ""
    );
  };
  const selectedType = entry.benefit_type;

  const benefitTypeChoiceKeys: Array<keyof typeof EmployerBenefitType> = [
    "shortTermDisability",
    "permanentDisability",
    "familyOrMedicalLeave",
  ];

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps(`employer_benefits[${index}].benefit_type`)}
        choices={benefitTypeChoiceKeys.map((benefitTypeKey) => {
          return {
            checked: selectedType === EmployerBenefitType[benefitTypeKey],
            label: t("pages.claimsEmployerBenefitsDetails.choiceLabel", {
              context: benefitTypeKey,
            }),
            hint:
              benefitTypeKey !== "permanentDisability"
                ? t("pages.claimsEmployerBenefitsDetails.choiceHint", {
                    context: benefitTypeKey,
                  })
                : null,
            value: EmployerBenefitType[benefitTypeKey],
          };
        })}
        label={t("pages.claimsEmployerBenefitsDetails.typeLabel")}
        type="radio"
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
          `employer_benefits[${index}].benefit_start_date`,
          `employer_benefits[${index}].benefit_end_date`,
        ]}
        clearField={clearField}
        getField={getEntryField}
        updateFields={updateFields}
        visible={get(entry, "is_full_salary_continuous") === true}
      >
        <Fieldset>
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
        </Fieldset>
      </ConditionalContent>
    </React.Fragment>
  );
};

export default withBenefitsApplication(EmployerBenefitsDetails);
