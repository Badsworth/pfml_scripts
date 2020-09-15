import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
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

const EmployerBenefit = ({ benefit }) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(benefit);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );
  const amendBenefit = (field, value) => {
    setAmendment({
      ...amendment,
      [field]: value,
    });
  };
  const benefitType = findKeyByValue(EmployerBenefitType, benefit.benefit_type);
  const getBenefitAmountByType = () => {
    return benefit.benefit_type === EmployerBenefitType.paidLeave
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
      {isAmendmentFormDisplayed && (
        <tr>
          <td
            colSpan="2"
            className="padding-top-2 padding-bottom-2 padding-left-0"
          >
            <AmendmentForm
              onCancel={() => {
                setIsAmendmentFormDisplayed(false);
                setAmendment(benefit);
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
                  amendBenefit("benefit_start_date", e.target.value)
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
                  amendBenefit("benefit_end_date", e.target.value)
                }
                value={amendment.benefit_end_date}
                label={t("components.amendmentForm.question_benefitEndDate")}
                name="benefit-end-date-amendment"
                dayLabel={t("components.form.dateInputDayLabel")}
                monthLabel={t("components.form.dateInputMonthLabel")}
                yearLabel={t("components.form.dateInputYearLabel")}
                smallLabel
              />
              <InputText
                onChange={(e) =>
                  amendBenefit("benefit_amount_dollars", e.target.value)
                }
                name="benefit-amount-amendment"
                value={amendment.benefit_amount_dollars}
                label={t("components.amendmentForm.question_benefitAmount")}
                type="number"
                width="medium"
                smallLabel
              />
            </AmendmentForm>
          </td>
          <td colSpan="2" />
        </tr>
      )}
    </React.Fragment>
  );
};

EmployerBenefit.propTypes = {
  benefit: PropTypes.object.isRequired,
};

export default EmployerBenefit;
