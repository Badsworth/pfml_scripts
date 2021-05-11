import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
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
  "claim.employer_benefits",
  "claim.employer_benefits[*].benefit_amount_dollars",
  "claim.employer_benefits[*].benefit_amount_frequency",
  "claim.employer_benefits[*].benefit_end_date",
  "claim.employer_benefits[*].benefit_start_date",
  "claim.employer_benefits[*].benefit_type",
];

export const EmployerBenefitsDetails = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const initialEntries = pick(props, fields).claim;
  const useInitialEntries = useRef(true);
  // If the claim doesn't have any employer benefits pre-populate the first one so that
  // it renders in the RepeatableFieldset below
  if (initialEntries.employer_benefits.length === 0) {
    initialEntries.employer_benefits = [new EmployerBenefit()];
  }
  const { formState, updateFields } = useFormState(initialEntries);
  const employer_benefits = get(formState, "employer_benefits");

  useEffect(() => {
    // Don't bother calling updateFields() when the page first renders
    if (useInitialEntries.current) {
      useInitialEntries.current = false;
      return;
    }
    // When there's a validation error, we get back the list of employer_benefits with employer_benefit_ids from the API
    // When claim.employer_benefits updates, we also need to update the formState values to include the employer_benefit_ids,
    // so on subsequent submits, we don't create new employer_benefit records
    updateFields({ employer_benefits: claim.employer_benefits });
  }, [claim.employer_benefits, updateFields]);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const handleAddClick = () => {
    // Add a new blank entry
    const updatedEntries = employer_benefits.concat([new EmployerBenefit()]);
    updateFields({ employer_benefits: updatedEntries });
  };

  const otherLeaves = appLogic.otherLeaves;
  const handleRemoveClick = async (entry, index) => {
    let entrySavedToApi = !!entry.employer_benefit_id;
    if (entrySavedToApi) {
      // Try to delete the entry from the API
      const success = await otherLeaves.removeEmployerBenefit(
        claim.application_id,
        entry.employer_benefit_id
      );
      entrySavedToApi = !success;
    }

    if (!entrySavedToApi) {
      const updatedEntries = [...employer_benefits];
      updatedEntries.splice(index, 1);
      updateFields({ employer_benefits: updatedEntries });
    }
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
        limit={3}
        limitMessage={t("pages.claimsEmployerBenefitsDetails.limitMessage")}
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
  const { entry, getFunctionalInputProps, index } = props;
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
          "paidLeave",
          "shortTermDisability",
          "permanentDisability",
          "familyOrMedicalLeave",
        ].map((benefitTypeKey) => {
          return {
            checked: selectedType === EmployerBenefitType[benefitTypeKey],
            label: t("pages.claimsEmployerBenefitsDetails.choiceLabel", {
              context: benefitTypeKey,
            }),
            hint: t("pages.claimsEmployerBenefitsDetails.choiceHint", {
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
        smallLabel
      />
      <Fieldset>
        <FormLabel
          component="legend"
          small
          optionalText={t("components.form.optional")}
        >
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
          width="medium"
          smallLabel
        />
        <Dropdown
          {...getFunctionalInputProps(
            `employer_benefits[${index}].benefit_amount_frequency`
          )}
          choices={benefitFrequencyChoices}
          label={t("pages.claimsEmployerBenefitsDetails.amountFrequencyLabel")}
          labelClassName="text-normal margin-top-0"
          formGroupClassName="margin-top-1"
          smallLabel
        />
      </Fieldset>
    </React.Fragment>
  );
};

EmployerBenefitCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.object.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withBenefitsApplication(EmployerBenefitsDetails);
