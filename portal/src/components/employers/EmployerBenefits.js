import AmendableEmployerBenefit from "./AmendableEmployerBenefit";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
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
  const { appErrors, employerBenefits, onChange } = props;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersEmployerBenefits.header")}
      </ReviewHeading>
      <Table className="width-full">
        <caption>
          <p className="text-normal">
            <Trans
              i18nKey="components.employersEmployerBenefits.caption"
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
          <p>{t("components.employersEmployerBenefits.tableName")}</p>
        </caption>
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersEmployerBenefits.dateRangeLabel")}
            </th>
            <th scope="col">
              {t("components.employersEmployerBenefits.benefitTypeLabel")}
            </th>
            <th scope="col" colSpan="2">
              {t("components.employersEmployerBenefits.detailsLabel")}
            </th>
          </tr>
        </thead>
        <tbody>
          {employerBenefits.length ? (
            employerBenefits.map((employerBenefit) => (
              <AmendableEmployerBenefit
                appErrors={appErrors}
                employerBenefit={employerBenefit}
                key={employerBenefit.employer_benefit_id}
                onChange={onChange}
              />
            ))
          ) : (
            <tr>
              <th scope="row">
                {t("components.employersEmployerBenefits.noneReported")}
              </th>
              <td colSpan="2" />
            </tr>
          )}
        </tbody>
      </Table>
      <p>{t("components.employersEmployerBenefits.commentInstructions")}</p>
    </React.Fragment>
  );
};

EmployerBenefits.propTypes = {
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  employerBenefits: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit)),
  onChange: PropTypes.func.isRequired,
};

export default EmployerBenefits;
