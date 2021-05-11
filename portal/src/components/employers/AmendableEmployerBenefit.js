import EmployerBenefit, {
  EmployerBenefitFrequency,
} from "../../models/EmployerBenefit";
import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../ConditionalContent";
import Dropdown from "../Dropdown";
import Heading from "../Heading";
import InputDate from "../InputDate";
import InputNumber from "../InputNumber";
import PropTypes from "prop-types";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display an employer benefit and amendment form
 * in the Leave Admin claim review page.
 */

const AmendableEmployerBenefit = ({ appErrors, employerBenefit, onChange }) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(employerBenefit);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );

  /**
   * Update amendment state and sends to `review.js` (dates, dollars, frequency)
   * For benefit amount dollars, sets invalid input to 0
   */
  const amendBenefit = (id, field, value) => {
    let formattedValue = value;
    if (field === "benefit_amount_dollars") {
      // Same logic as SupportingWorkingDetails
      // Invalid input will default to 0, validation error message is upcoming
      const isInvalid = value === "0" || !parseFloat(value);
      value = isInvalid ? 0 : value;
      formattedValue = isInvalid ? 0 : parseFloat(value.replace(/,/g, ""));
    }
    setAmendment({
      ...amendment,
      [field]: value, // display commmas in field
    });
    onChange({ employer_benefit_id: id, [field]: formattedValue });
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

  const startDateErrMsg = appErrors.fieldErrorMessage(
    `employer_benefits[${employerBenefit.employer_benefit_id}].benefit_start_date`
  );
  const leaveDateErrMsg = appErrors.fieldErrorMessage(
    `employer_benefits[${employerBenefit.employer_benefit_id}].benefit_end_date`
  );

  return (
    <React.Fragment>
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
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <tr>
          <td
            colSpan="4"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              onCancel={() => {
                setIsAmendmentFormDisplayed(false);
                setAmendment(employerBenefit);
                onChange(employerBenefit);
              }}
            >
              <Heading level="4">{employerBenefit.benefit_type}</Heading>
              <InputDate
                onChange={(e) =>
                  amendBenefit(
                    employerBenefit.employer_benefit_id,
                    "benefit_start_date",
                    e.target.value
                  )
                }
                value={amendment.benefit_start_date}
                label={t("components.amendmentForm.question_benefitStartDate")}
                errorMsg={startDateErrMsg}
                name={`employer_benefits[${employerBenefit.employer_benefit_id}].benefit_start_date`}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputDate
                onChange={(e) =>
                  amendBenefit(
                    employerBenefit.employer_benefit_id,
                    "benefit_end_date",
                    e.target.value
                  )
                }
                value={amendment.benefit_end_date}
                label={t("components.amendmentForm.question_benefitEndDate")}
                errorMsg={leaveDateErrMsg}
                name={`employer_benefits[${employerBenefit.employer_benefit_id}].benefit_end_date`}
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputNumber
                onChange={(e) =>
                  amendBenefit(
                    employerBenefit.employer_benefit_id,
                    "benefit_amount_dollars",
                    e.target.value
                  )
                }
                name="benefit-amount-amendment"
                value={amendment.benefit_amount_dollars}
                label={t("components.amendmentForm.question_benefitAmount")}
                mask="currency"
                width="medium"
                smallLabel
              />
              <Dropdown
                choices={getAllBenefitFrequencies()}
                label={t("components.amendmentForm.question_benefitFrequency")}
                name="benefit-frequency-amendment"
                onChange={(e) =>
                  amendBenefit(
                    employerBenefit.employer_benefit_id,
                    "benefit_amount_frequency",
                    e.target.value
                  )
                }
                class="margin-top-0"
                value={amendment.benefit_amount_frequency}
                hideEmptyChoice
                smallLabel
              />
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
  onChange: PropTypes.func.isRequired,
};

export default AmendableEmployerBenefit;
