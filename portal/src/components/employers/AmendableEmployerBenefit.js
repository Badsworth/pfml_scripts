import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../ConditionalContent";
import Dropdown from "../Dropdown";
import Fieldset from "../Fieldset";
import FormLabel from "../FormLabel";
import Heading from "../Heading";
import InputChoiceGroup from "../InputChoiceGroup";
import InputCurrency from "../InputCurrency";
import InputDate from "../InputDate";
import PropTypes from "prop-types";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";

/**
 * Display an employer benefit and amendment form
 * in the Leave Admin claim review page.
 */

const AmendableEmployerBenefit = ({
  appErrors,
  isAddedByLeaveAdmin,
  employerBenefit,
  onChange,
  onRemove,
  shouldShowV2,
}) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(employerBenefit);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );

  const getFieldPath = (field) =>
    `employer_benefits[${amendment.employer_benefit_id}].${field}`;

  const getErrorMessage = (field) =>
    appErrors.fieldErrorMessage(getFieldPath(field));

  const getFormattedValue = (field, value) => {
    if (field === "benefit_start_date" || field === "benefit_end_date") {
      // happens if a user starts typing a date, then removes it
      // these fields aren't required, and sending an empty string returns an "invalid date" error
      return value === "" ? null : value;
    }

    return value;
  };

  /**
   * Update amendment state and sends to `review.js` (dates, dollars, frequency)
   * For benefit amount dollars, sets invalid input to 0
   */
  const amendBenefit = (field, value) => {
    const formStateField = isAddedByLeaveAdmin
      ? "addedBenefits"
      : "amendedBenefits";
    const formattedValue = getFormattedValue(field, value);
    setAmendment({
      ...amendment,
      [field]: value, // display commmas in field
    });
    onChange(
      {
        employer_benefit_id: employerBenefit.employer_benefit_id,
        [field]: formattedValue,
      },
      formStateField
    );
  };

  /**
   * Get benefit_amount_frequency options for the input's `choices` prop
   * Includes an option if frequency is null or "Unknown"
   * (e.g. [{ label: "", value: "" }])
   * @returns {Array}
   */
  const getAllBenefitFrequencies = () => {
    return Object.values(EmployerBenefitFrequency).map((frequency) => {
      return {
        label: t("components.employersEmployerBenefits.amountFrequency", {
          context: findKeyByValue(EmployerBenefitFrequency, frequency),
        }),
        value: frequency,
      };
    });
  };

  /**
   * Get content based on dollars and frequency  (e.g. $10.00 per day)
   * Displays dollar amount if frequency is null or "Unknown"
   * @returns {string}
   */
  const getBenefitAmountByType = () => {
    const {
      benefit_amount_dollars,
      benefit_amount_frequency,
    } = employerBenefit;
    return t("components.employersEmployerBenefits.amountPerFrequency", {
      context: findKeyByValue(
        EmployerBenefitFrequency,
        benefit_amount_frequency
      ),
      amount: benefit_amount_dollars,
    });
  };

  const handleCancelAmendment = () => {
    setIsAmendmentFormDisplayed(false);
    setAmendment(employerBenefit);
    onChange(employerBenefit, "amendedBenefits");
  };

  const handleDeleteAddition = () => {
    onRemove(amendment);
  };

  const addOrAmend = isAddedByLeaveAdmin ? "add" : "amend";

  const additionFormClasses = "bg-white";
  const amendmentFormClasses = "bg-base-lightest border-base-lighter";
  const className = isAddedByLeaveAdmin
    ? additionFormClasses
    : amendmentFormClasses;

  const onDestroy = isAddedByLeaveAdmin
    ? handleDeleteAddition
    : handleCancelAmendment;

  const BenefitDetailsRow = () => (
    <tr>
      <th scope="row">
        {formatDateRange(
          employerBenefit.benefit_start_date,
          employerBenefit.benefit_end_date
        )}
      </th>
      <td>{employerBenefit.benefit_type}</td>
      <td>{getBenefitAmountByType()}</td>
      <td>
        <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
      </td>
    </tr>
  );

  return (
    <React.Fragment>
      {!isAddedByLeaveAdmin && <BenefitDetailsRow />}
      <ConditionalContent
        visible={isAddedByLeaveAdmin || isAmendmentFormDisplayed}
      >
        <tr>
          <td colSpan="1" className="padding-y-2 padding-left-0">
            <AmendmentForm
              className={className}
              destroyButtonLabel={t(
                "components.employersAmendableEmployerBenefit.destroyButtonLabel",
                { context: addOrAmend }
              )}
              onDestroy={onDestroy}
            >
              <Heading level="4">
                {t("components.employersAmendableEmployerBenefit.heading", {
                  context: addOrAmend,
                })}
              </Heading>
              <p>
                {t("components.employersAmendableEmployerBenefit.subtitle", {
                  context: addOrAmend,
                })}
              </p>
              <ConditionalContent visible={shouldShowV2}>
                <InputChoiceGroup
                  name={getFieldPath("benefit_type")}
                  smallLabel
                  label={t(
                    "components.employersAmendableEmployerBenefit.benefitTypeLabel"
                  )}
                  type="radio"
                  choices={[
                    "shortTermDisability",
                    "permanentDisability",
                    "familyOrMedicalLeave",
                  ].map((benefitTypeKey) => {
                    return {
                      label: t(
                        "components.employersAmendableEmployerBenefit.choiceLabel",
                        { context: benefitTypeKey }
                      ),
                      hint:
                        benefitTypeKey !== "permanentDisability" &&
                        t(
                          "components.employersAmendableEmployerBenefit.choiceHint",
                          {
                            context: benefitTypeKey,
                          }
                        ),
                      value: EmployerBenefitType[benefitTypeKey],
                      checked:
                        get(amendment, "benefit_type") ===
                        EmployerBenefitType[benefitTypeKey],
                    };
                  })}
                  onChange={(e) => {
                    amendBenefit("benefit_type", e.target.value);
                  }}
                />
              </ConditionalContent>
              <InputDate
                name={getFieldPath("benefit_start_date")}
                smallLabel
                label={t(
                  "components.employersAmendableEmployerBenefit.benefitStartDateLabel"
                )}
                value={get(amendment, "benefit_start_date")}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                errorMsg={getErrorMessage("benefit_start_date")}
                onChange={(e) => {
                  amendBenefit("benefit_start_date", e.target.value);
                }}
              />
              <InputDate
                smallLabel
                label={t(
                  "components.employersAmendableEmployerBenefit.benefitEndDateLabel"
                )}
                optionalText={t("components.form.optional")}
                errorMsg={getErrorMessage("benefit_end_date")}
                name={getFieldPath("benefit_end_date")}
                value={get(amendment, "benefit_end_date")}
                onChange={(e) => {
                  amendBenefit("benefit_end_date", e.target.value);
                }}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
              />
              <ConditionalContent visible={shouldShowV2}>
                <InputChoiceGroup
                  name={getFieldPath("is_full_salary_continuous")}
                  smallLabel
                  label={t(
                    "components.employersAmendableEmployerBenefit.isFullSalaryContinuousLabel"
                  )}
                  hint={t(
                    "components.employersAmendableEmployerBenefit.isFullSalaryContinuousHint"
                  )}
                  optionalText={t("components.form.optional")}
                  onChange={(e) => {
                    amendBenefit("is_full_salary_continuous", e.target.value);
                  }}
                  errorMsg={getErrorMessage("is_full_salary_continuous")}
                  type="radio"
                  choices={[
                    {
                      checked:
                        get(amendment, "is_full_salary_continuous") === "true",
                      label: t(
                        "components.employersAmendableEmployerBenefit.choiceYes"
                      ),
                      value: "true",
                    },
                    {
                      checked:
                        get(amendment, "is_full_salary_continuous") === "false",
                      label: t(
                        "components.employersAmendableEmployerBenefit.choiceNo"
                      ),
                      value: "false",
                    },
                  ]}
                />
                <ConditionalContent
                  visible={
                    get(amendment, "is_full_salary_continuous") === "false"
                  }
                >
                  <Fieldset>
                    <FormLabel
                      component="legend"
                      small
                      optionalText={t("components.form.optional")}
                    >
                      {t(
                        "components.employersAmendableEmployerBenefit.employeeAmountReceivedLabel"
                      )}
                    </FormLabel>
                    <InputCurrency
                      name={getFieldPath("benefit_amount_dollars")}
                      smallLabel
                      label={t(
                        "components.employersAmendableEmployerBenefit.benefitAmountDollarsLabel"
                      )}
                      labelClassName="text-normal"
                      width="small"
                      errorMsg={getErrorMessage("benefit_amount_dollars")}
                      value={get(amendment, "benefit_amount_dollars")}
                      onChange={(e) => {
                        amendBenefit("benefit_amount_dollars", e.target.value);
                      }}
                    />
                    <Dropdown
                      name={getFieldPath("benefit_amount_frequency")}
                      smallLabel
                      label={t(
                        "components.employersAmendableEmployerBenefit.amountFrequencyLabel"
                      )}
                      labelClassName="text-normal"
                      choices={getAllBenefitFrequencies()}
                      errorMsg={getErrorMessage("benefit_amount_frequency")}
                      value={get(amendment, "benefit_amount_frequency")}
                      onChange={(e) => {
                        amendBenefit(
                          "benefit_amount_frequency",
                          e.target.value
                        );
                      }}
                    />
                  </Fieldset>
                </ConditionalContent>
              </ConditionalContent>
            </AmendmentForm>
          </td>
        </tr>
      </ConditionalContent>
    </React.Fragment>
  );
};

AmendableEmployerBenefit.propTypes = {
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  employerBenefit: PropTypes.instanceOf(EmployerBenefit).isRequired,
  isAddedByLeaveAdmin: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  shouldShowV2: PropTypes.bool.isRequired,
};

export default AmendableEmployerBenefit;
