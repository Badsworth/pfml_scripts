import AmendableEmployerBenefit from "./AmendableEmployerBenefit";
import EmployerBenefit from "../../models/EmployerBenefit";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import { useTranslation } from "../../locales/i18n";

/**
 * Display all employer benefits
 * in the Leave Admin claim review page.
 */

const EmployerBenefits = (props) => {
  const { t } = useTranslation();
  const { employerBenefits, onChange } = props;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("pages.employersClaimsReview.employerBenefits.header")}
      </ReviewHeading>
      <Table className="width-full">
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
          {employerBenefits.length ? (
            employerBenefits.map((employerBenefit) => (
              <AmendableEmployerBenefit
                employerBenefit={employerBenefit}
                key={employerBenefit.id}
                onChange={onChange}
              />
            ))
          ) : (
            <tr>
              <th scope="row">
                {t("pages.employersClaimsReview.noneReported")}
              </th>
              <td colSpan="2" />
            </tr>
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

EmployerBenefits.propTypes = {
  employerBenefits: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit)),
  onChange: PropTypes.func.isRequired,
};

export default EmployerBenefits;
