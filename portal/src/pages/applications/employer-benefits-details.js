import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
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

export const fields = ["claim.employer_benefits"];

export const EmployerBenefitDetails = (props) => {
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

  const handleSave = async () => {
    // Make sure benefit_amount_dollars is a number.
    // TODO (CP-1528): Refactor Currency Masking
    // There's a similar function in OtherIncomedDetails.
    const patchData = cloneDeep(formState);
    patchData.employer_benefits = patchData.employer_benefits.map((benefit) => {
      const val = benefit.benefit_amount_dollars;
      const number =
        isFinite(val) || isNil(val) ? val : Number(val.replace(/,/g, ""));
      return { ...benefit, benefit_amount_dollars: number };
    });
    await appLogic.claims.update(claim.application_id, patchData);
  };

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

      <LeaveDatesAlert
        startDate={claim.leaveStartDate}
        endDate={claim.leaveEndDate}
        headingLevel="3"
      />

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

  const benefitFrequencyChoices = Object.entries(EmployerBenefitFrequency).map(
    ([frequencyKey, frequency]) => {
      return {
        label: t("pages.claimsEmployerBenefitDetails.amountFrequency", {
          context: frequencyKey,
        }),
        value: frequency,
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
            label: t("pages.claimsEmployerBenefitDetails.choiceLabel", {
              context: benefitTypeKey,
            }),
            hint: t("pages.claimsEmployerBenefitDetails.choiceHint", {
              context: benefitTypeKey,
            }),
            value: EmployerBenefitType[benefitTypeKey],
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
        label={t("pages.claimsEmployerBenefitDetails.endDateLabel")}
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
          {t("pages.claimsEmployerBenefitDetails.amountLegend")}
        </FormLabel>
        <div className="grid-row grid-gap">
          <div className="mobile-lg:grid-col-6">
            <InputText
              {...getFunctionalInputProps(
                `employer_benefits[${index}].benefit_amount_dollars`
              )}
              inputMode="numeric"
              label={t("pages.claimsEmployerBenefitDetails.amountLabel")}
              labelClassName="text-normal margin-top-05"
              mask="currency"
              smallLabel
            />
          </div>
          <div className="mobile-lg:grid-col-6">
            <Dropdown
              {...getFunctionalInputProps(
                `employer_benefits[${index}].benefit_amount_frequency`
              )}
              choices={benefitFrequencyChoices}
              label={t(
                "pages.claimsEmployerBenefitDetails.amountFrequencyLabel"
              )}
              labelClassName="text-normal margin-top-05"
              smallLabel
            />
          </div>
        </div>
      </Fieldset>
    </React.Fragment>
  );
};

EmployerBenefitCard.propTypes = {
  index: PropTypes.number.isRequired,
  entry: PropTypes.object.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default withClaim(EmployerBenefitDetails);
