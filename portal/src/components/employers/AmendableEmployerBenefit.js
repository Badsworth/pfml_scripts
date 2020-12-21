import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConditionalContent from "../ConditionalContent";
import Dropdown from "../Dropdown";
import InputDate from "../InputDate";
import InputText from "../InputText";
import PropTypes from "prop-types";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display an employer benefit and amendment form
 * in the Leave Admin claim review page.
 */

const AmendableEmployerBenefit = ({ employerBenefit, onChange }) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(employerBenefit);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );
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
  const isPaidLeave =
    employerBenefit.benefit_type === EmployerBenefitType.paidLeave;
  const getBenefitAmountByType = () => {
    const {
      benefit_amount_dollars,
      benefit_amount_frequency,
    } = employerBenefit;
    const hasBenefitAmountDetails =
      benefit_amount_dollars && benefit_amount_frequency;
    return isPaidLeave || !hasBenefitAmountDetails
      ? t("pages.employersClaimsReview.notApplicable")
      : t("pages.employersClaimsReview.employerBenefits.amountPerFrequency", {
          context: findKeyByValue(
            EmployerBenefitFrequency,
            benefit_amount_frequency
          ),
          amount: benefit_amount_dollars,
        });
  };
  const getAllBenefitFrequencies = () => {
    return Object.values(EmployerBenefitFrequency).map((frequency) => {
      return {
        label: t(
          "pages.employersClaimsReview.employerBenefits.employerBenefitFrequencyValue",
          {
            context: findKeyByValue(EmployerBenefitFrequency, frequency),
          }
        ),
        value: frequency,
      };
    });
  };

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
              <p>{employerBenefit.benefit_type}</p>
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
                name="benefit-start-date-amendment"
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
                name="benefit-end-date-amendment"
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              {!isPaidLeave && (
                <React.Fragment>
                  <InputText
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
                    label={t(
                      "components.amendmentForm.question_benefitFrequency"
                    )}
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
                </React.Fragment>
              )}
            </AmendmentForm>
          </td>
        </tr>
      </ConditionalContent>
    </React.Fragment>
  );
};

AmendableEmployerBenefit.propTypes = {
  employerBenefit: PropTypes.instanceOf(EmployerBenefit).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default AmendableEmployerBenefit;
