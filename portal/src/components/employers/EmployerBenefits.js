import AmendableEmployerBenefit from "./AmendableEmployerBenefit";
import EmployerBenefit from "../../models/EmployerBenefit";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import { Trans } from "react-i18next";
import routes from "../../routes";
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
          <p className="text-normal">
            <Trans
              i18nKey="pages.employersClaimsReview.employerBenefits.caption"
              components={{
                "reductions-overview-link": (
                  <a
                    href={routes.external.massgov.reductionsOverview}
                    target="_blank"
                    rel="noopener"
                  />
                ),
              }}
            />
          </p>
          <p>{t("pages.employersClaimsReview.employerBenefits.tableName")}</p>
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
      <p>
        {t("pages.employersClaimsReview.employerBenefits.commentInstructions")}
      </p>
    </React.Fragment>
  );
};

EmployerBenefits.propTypes = {
  employerBenefits: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit)),
  onChange: PropTypes.func.isRequired,
};

export default EmployerBenefits;
