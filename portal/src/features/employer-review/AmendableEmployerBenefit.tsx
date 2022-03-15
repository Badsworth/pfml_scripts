import EmployerBenefit, {
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import React, { useRef, useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "../../components/AmendmentForm";
import ConditionalContent from "../../components/ConditionalContent";
import Heading from "../../components/core/Heading";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputDate from "../../components/core/InputDate";
import findErrorMessageForField from "../../utils/findErrorMessageForField";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import getInputValueFromEvent from "../../utils/getInputValueFromEvent";
import useAutoFocusEffect from "../../hooks/useAutoFocusEffect";
import { useTranslation } from "../../locales/i18n";

interface AmendableEmployerBenefitProps {
  errors: Error[];
  employerBenefit: EmployerBenefit;
  isAddedByLeaveAdmin: boolean;
  onChange: (
    arg: EmployerBenefit | { [key: string]: unknown },
    arg2: string
  ) => void;
  onRemove: (arg: EmployerBenefit) => void;
  shouldShowV2: boolean;
}

/**
 * Display an employer benefit and amendment form
 * in the Leave Admin claim review page.
 */

const AmendableEmployerBenefit = ({
  errors,
  isAddedByLeaveAdmin,
  employerBenefit,
  onChange,
  onRemove,
  shouldShowV2,
}: AmendableEmployerBenefitProps) => {
  const { t } = useTranslation();
  const [amendment, setAmendment] = useState(employerBenefit);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] =
    useState(isAddedByLeaveAdmin);
  const containerRef = useRef<HTMLTableRowElement>(null);
  useAutoFocusEffect({ containerRef, isAmendmentFormDisplayed });

  const getFieldPath = (field: string) =>
    `employer_benefits[${amendment.employer_benefit_id}].${field}`;

  const getErrorMessage = (field: string) =>
    findErrorMessageForField(errors, getFieldPath(field));

  /**
   * Update amendment state and sends to `review.js` (dates, dollars, frequency)
   * For benefit amount dollars, sets invalid input to 0
   */
  const amendBenefit = (
    field: string,
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
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
    <tr data-testid="benefit-details-row">
      <th
        scope="row"
        data-label={t("components.employersEmployerBenefits.dateRangeLabel")}
      >
        {formatDateRange(
          employerBenefit.benefit_start_date,
          employerBenefit.benefit_end_date
        )}
      </th>
      <td
        data-label={t("components.employersEmployerBenefits.benefitTypeLabel")}
      >
        {employerBenefit.benefit_type}
      </td>
      <td>
        <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
      </td>
    </tr>
  );

  const benefitTypeKeys: Array<keyof typeof EmployerBenefitType> = [
    "shortTermDisability",
    "permanentDisability",
    "familyOrMedicalLeave",
  ];

  return (
    <React.Fragment>
      {!isAddedByLeaveAdmin && <BenefitDetailsRow />}
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <tr ref={containerRef} data-testid="added-benefit-details-row">
          <td colSpan={4} className="padding-y-2 padding-left-0">
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
                  choices={benefitTypeKeys.map((benefitTypeKey) => {
                    return {
                      label: t(
                        "components.employersAmendableEmployerBenefit.choiceLabel",
                        { context: benefitTypeKey }
                      ),
                      hint:
                        benefitTypeKey !== "permanentDisability"
                          ? t(
                              "components.employersAmendableEmployerBenefit.choiceHint",
                              {
                                context: benefitTypeKey,
                              }
                            )
                          : null,
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
                visible={get(amendment, "is_full_salary_continuous") === true}
              >
                <InputDate
                  name={getFieldPath("benefit_start_date")}
                  data-test="benefit-start-date-input"
                  smallLabel
                  label={t(
                    "components.employersAmendableEmployerBenefit.benefitStartDateLabel"
                  )}
                  value={get(amendment, "benefit_start_date") || ""}
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
                  value={get(amendment, "benefit_end_date") || ""}
                  onChange={(e) => {
                    amendBenefit("benefit_end_date", e);
                  }}
                  dayLabel={t("components.form.dateInputDayLabel")}
                  monthLabel={t("components.form.dateInputMonthLabel")}
                  yearLabel={t("components.form.dateInputYearLabel")}
                />
              </ConditionalContent>
            </AmendmentForm>
          </td>
        </tr>
      </ConditionalContent>
    </React.Fragment>
  );
};

export default AmendableEmployerBenefit;
