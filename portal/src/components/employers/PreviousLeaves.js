import AmendablePreviousLeave from "./AmendablePreviousLeave";
import Details from "../Details";
import PreviousLeave from "../../models/PreviousLeave";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

/**
 * Display past leaves taken by the employee
 * in the Leave Admin claim review page.
 */

const PreviousLeaves = (props) => {
  const { t } = useTranslation();
  const { previousLeaves, onChange } = props;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("pages.employersClaimsReview.previousLeaves.header")}
      </ReviewHeading>
      <p>
        <Trans
          i18nKey="pages.employersClaimsReview.previousLeaves.explanation"
          components={{
            "calculate-reductions-link": (
              <a
                href={routes.external.massgov.calculateReductions}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
      <Details
        label={t("pages.employersClaimsReview.previousLeaves.detailsLabel")}
        className="text-bold"
      >
        <p>
          {t(
            "pages.employersClaimsReview.previousLeaves.qualifyingReasonContent"
          )}
        </p>
        <ul className="usa-list">
          <li>
            <Trans
              i18nKey="pages.employersClaimsReview.previousLeaves.qualifyingReason_manageHealth"
              components={{
                "mass-benefits-guide-serious-health-condition-link": (
                  <a
                    target="_blank"
                    rel="noopener"
                    href={
                      routes.external.massgov
                        .benefitsGuide_seriousHealthCondition
                    }
                  />
                ),
              }}
            />
          </li>
          <li>
            {t(
              "pages.employersClaimsReview.previousLeaves.qualifyingReason_bondWithChild"
            )}
          </li>
          <li>
            {t(
              "pages.employersClaimsReview.previousLeaves.qualifyingReason_activeDuty"
            )}
          </li>
          <li>
            {t(
              "pages.employersClaimsReview.previousLeaves.qualifyingReason_careForFamilyMilitary"
            )}
          </li>
          <li>
            <Trans
              i18nKey="pages.employersClaimsReview.previousLeaves.qualifyingReason_careForFamilyMedical"
              components={{
                "mass-benefits-guide-serious-health-condition-link": (
                  <a
                    target="_blank"
                    rel="noopener"
                    href={
                      routes.external.massgov
                        .benefitsGuide_seriousHealthCondition
                    }
                  />
                ),
              }}
            />
          </li>
        </ul>
      </Details>
      <Table>
        <thead>
          <tr>
            <th colSpan="3" scope="col">
              {t(
                "pages.employersClaimsReview.previousLeaves.tableHeader_dateRange"
              )}
            </th>
          </tr>
        </thead>
        <tbody>
          {previousLeaves.length ? (
            <React.Fragment>
              {previousLeaves.map((leavePeriod) => {
                return (
                  <AmendablePreviousLeave
                    leavePeriod={leavePeriod}
                    key={leavePeriod.previous_leave_id}
                    onChange={onChange}
                  />
                );
              })}
            </React.Fragment>
          ) : (
            <tr>
              <th scope="row">
                {t("pages.employersClaimsReview.noneReported")}
              </th>
              <td colSpan="3" />
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

PreviousLeaves.propTypes = {
  previousLeaves: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave)),
  onChange: PropTypes.func.isRequired,
};

export default PreviousLeaves;
