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
import getInputValueFromEvent from "../../utils/getInputValueFromEvent";
import useAutoFocusEffect from "../../hooks/useAutoFocusEffect";
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
    isAddedByLeaveAdmin
  );
  const containerRef = React.createRef();
  useAutoFocusEffect({ containerRef, isAmendmentFormDisplayed });

  const getFieldPath = (field) =>
    `employer_benefits[${amendment.employer_benefit_id}].${field}`;

  const getErrorMessage = (field) =>
    appErrors.fieldErrorMessage(getFieldPath(field));

  /**
   * Update amendment state and sends to `review.js` (dates, dollars, frequency)
   * For benefit amount dollars, sets invalid input to 0
   */
  const amendBenefit = (field, event) => {
    const formStateField = isAddedByLeaveAdmin
      ? "addedBenefits"
      : "amendedBenefits";
    const value = getInputValueFromEvent(event);

    setAmendment({
      ...amendment,
      [field]: value,
    });
    onChange(
      {
        employer_benefit_id: employerBenefit.employer_benefit_id,
        [field]: value,
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
      is_full_salary_continuous,
    } = employerBenefit;

    if (is_full_salary_continuous) {
      return t("components.employersEmployerBenefits.fullSalaryContinuous");
    } else if (
      benefit_amount_dollars === 0 &&
      benefit_amount_frequency === EmployerBenefitFrequency.unknown
    ) {
      return t("components.employersEmployerBenefits.noAmountReported");
    }

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
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <tr ref={containerRef}>
          <td colSpan="4" className="padding-y-2 padding-left-0">
            <AmendmentForm
              className={className}
              destroyButtonLabel={t(
                "components.employersAmendableEmployerBenefit.destroyButtonLabel",
                { context: addOrAmend }
              )}
              onDestroy={onDestroy}
            >
              <Heading level="4" size="3">
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
                  data-test="benefit-type-input"
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
                    amendBenefit("benefit_type", e);
                  }}
                />
              </ConditionalContent>
              <InputDate
                name={getFieldPath("benefit_start_date")}
                data-test="benefit-start-date-input"
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
                  amendBenefit("benefit_start_date", e);
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
                data-test="benefit-end-date-input"
                value={get(amendment, "benefit_end_date")}
                onChange={(e) => {
                  amendBenefit("benefit_end_date", e);
                }}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
              />
              <ConditionalContent visible={shouldShowV2}>
                <InputChoiceGroup
                  name={getFieldPath("is_full_salary_continuous")}
                  data-test="is-full-salary-continuous-input"
                  smallLabel
                  label={t(
                    "components.employersAmendableEmployerBenefit.isFullSalaryContinuousLabel"
                  )}
                  hint={t(
                    "components.employersAmendableEmployerBenefit.isFullSalaryContinuousHint"
                  )}
                  optionalText={t("components.form.optional")}
                  onChange={(e) => {
                    amendBenefit("is_full_salary_continuous", e);
                  }}
                  errorMsg={getErrorMessage("is_full_salary_continuous")}
                  type="radio"
                  choices={[
                    {
                      checked:
                        get(amendment, "is_full_salary_continuous") === true,
                      label: t(
                        "components.employersAmendableEmployerBenefit.choiceYes"
                      ),
                      value: "true",
                    },
                    {
                      checked:
                        get(amendment, "is_full_salary_continuous") === false,
                      label: t(
                        "components.employersAmendableEmployerBenefit.choiceNo"
                      ),
                      value: "false",
                    },
                  ]}
                />
              </ConditionalContent>
              <ConditionalContent
                visible={
                  !shouldShowV2 ||
                  get(amendment, "is_full_salary_continuous") === false
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
                    data-test="benefit-amount-dollars-input"
                    smallLabel
                    label={t(
                      "components.employersAmendableEmployerBenefit.benefitAmountDollarsLabel"
                    )}
                    labelClassName="text-normal"
                    width="small"
                    errorMsg={getErrorMessage("benefit_amount_dollars")}
                    value={get(amendment, "benefit_amount_dollars")}
                    onChange={(e) => {
                      amendBenefit("benefit_amount_dollars", e);
                    }}
                  />
                  <Dropdown
                    name={getFieldPath("benefit_amount_frequency")}
                    data-test="benefit-amount-frequency-input"
                    smallLabel
                    label={t(
                      "components.employersAmendableEmployerBenefit.amountFrequencyLabel"
                    )}
                    labelClassName="text-normal"
                    choices={getAllBenefitFrequencies()}
                    errorMsg={getErrorMessage("benefit_amount_frequency")}
                    value={get(amendment, "benefit_amount_frequency")}
                    onChange={(e) => {
                      amendBenefit("benefit_amount_frequency", e);
                    }}
                  />
                </Fieldset>
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
