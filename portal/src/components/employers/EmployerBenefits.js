import AmendLink from "./AmendLink";
import { EmployerBenefitType } from "../../models/EmployerBenefit";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display all employer benefits, regardless of whether the employee is using,
 * in the Leave Admin claim review page.
 */

const EmployerBenefits = (props) => {
  const { t } = useTranslation();
  const { employerBenefits } = props;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("pages.employersClaimsReview.employerBenefits.header")}
      </ReviewHeading>
      <Table>
        <caption>
          {t("pages.employersClaimsReview.employerBenefits.tableName")}
        </caption>
        <thead>
          <tr>
            <th scope="col">
              {t("pages.employersClaimsReview.employerBenefits.dateRangeLabel")}
            </th>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.employerBenefits.benefitTypeLabel"
              )}
            </th>
            <th scope="col" colSpan="2">
              {t("pages.employersClaimsReview.employerBenefits.detailsLabel")}
            </th>
          </tr>
        </thead>
        <tbody>
          {employerBenefits.map((benefit, index) => {
            return (
              <tr key={index}>
                <th scope="row">
                  {benefit.benefit_start_date && benefit.benefit_end_date
                    ? formatDateRange(
                        benefit.benefit_start_date,
                        benefit.benefit_end_date
                      )
                    : t("pages.employersClaimsReview.notApplicable")}
                </th>
                <td>
                  {t(
                    "pages.employersClaimsReview.employerBenefits.employerBenefitType",
                    {
                      context: findKeyByValue(
                        EmployerBenefitType,
                        benefit.benefit_type
                      ),
                    }
                  )}
                </td>
                <td>
                  {benefit.benefit_amount_dollars
                    ? benefit.benefit_amount_dollars
                    : t("pages.employersClaimsReview.none")}
                </td>
                <td>
                  <AmendLink />
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

EmployerBenefits.propTypes = {
  employerBenefits: PropTypes.array,
};

export default EmployerBenefits;
