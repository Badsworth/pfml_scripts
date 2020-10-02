import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConditionalContent from "../ConditionalContent";
import { EmployerBenefitType } from "../../models/EmployerBenefit";
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

const EmployerBenefit = ({ benefit, onChange }) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(benefit);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );
  const amendBenefit = (id, field, value) => {
    const formattedValue =
      field === "benefit_amount_dollars" ? parseInt(value) : value;
    setAmendment({
      ...amendment,
      [field]: value,
    });
    onChange({ id, [field]: formattedValue });
  };
  const benefitType = findKeyByValue(EmployerBenefitType, benefit.benefit_type);
  const isPaidLeave = benefit.benefit_type === EmployerBenefitType.paidLeave;
  const getBenefitAmountByType = () => {
    return isPaidLeave
      ? t("pages.employersClaimsReview.notApplicable")
      : benefit.benefit_amount_dollars;
  };

  return (
    <React.Fragment>
      <tr>
        <th scope="row">
          {formatDateRange(
            benefit.benefit_start_date,
            benefit.benefit_end_date
          )}
        </th>
        <td>
          {t(
            "pages.employersClaimsReview.employerBenefits.employerBenefitType",
            {
              context: benefitType,
            }
          )}
        </td>
        <td>{getBenefitAmountByType()}</td>
        <td>
          <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
        </td>
      </tr>
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <tr>
          <td
            colSpan="2"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              onCancel={() => {
                setIsAmendmentFormDisplayed(false);
                setAmendment(benefit);
                onChange(benefit);
              }}
            >
              <p>
                {t(
                  "pages.employersClaimsReview.employerBenefits.employerBenefitType",
                  {
                    context: benefitType,
                  }
                )}
              </p>
              <InputDate
                onChange={(e) =>
                  amendBenefit(benefit.id, "benefit_start_date", e.target.value)
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
                  amendBenefit(benefit.id, "benefit_end_date", e.target.value)
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
                <InputText
                  onChange={(e) =>
                    amendBenefit(
                      benefit.id,
                      "benefit_amount_dollars",
                      e.target.value
                    )
                  }
                  name="benefit-amount-amendment"
                  value={amendment.benefit_amount_dollars}
                  label={t("components.amendmentForm.question_benefitAmount")}
                  type="number"
                  width="medium"
                  smallLabel
                />
              )}
            </AmendmentForm>
          </td>
          <td colSpan="2" />
        </tr>
      </ConditionalContent>
    </React.Fragment>
  );
};

EmployerBenefit.propTypes = {
  benefit: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default EmployerBenefit;
