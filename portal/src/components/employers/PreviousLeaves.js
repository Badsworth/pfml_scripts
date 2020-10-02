import AmendablePreviousLeave from "./AmendablePreviousLeave";
import Details from "../Details";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
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
      <p>{t("pages.employersClaimsReview.previousLeaves.explanation")}</p>
      <Details
        label={t("pages.employersClaimsReview.previousLeaves.detailsLabel")}
      >
        <p>
          {t(
            "pages.employersClaimsReview.previousLeaves.qualifyingReasonContent"
          )}
        </p>
        <ul className="usa-list">
          <li>
            {t(
              "pages.employersClaimsReview.previousLeaves.qualifyingReason_manageHealth"
            )}
          </li>
          <li>
            {t(
              "pages.employersClaimsReview.previousLeaves.qualifyingReason_careForFamily"
            )}
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
        </ul>
      </Details>
      <Table className="width-full">
        <thead>
          <tr>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.previousLeaves.tableHeader_dateRange"
              )}
            </th>
            <th scope="col">
              {t("pages.employersClaimsReview.previousLeaves.tableHeader_days")}
            </th>
            <th scope="col" colSpan="2">
              {t(
                "pages.employersClaimsReview.previousLeaves.tableHeader_leaveType"
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
                    key={leavePeriod.id}
                    onChange={onChange}
                  />
                );
              })}
              <tr>
                <th scope="row" className="text-bold">
                  {t(
                    "pages.employersClaimsReview.previousLeaves.tableFooter_totalLeave"
                  )}
                </th>
                <td colSpan="2">
                  {t("pages.employersClaimsReview.durationBasis_days", {
                    numOfDays: t("pages.employersClaimsReview.notApplicable"),
                  })}
                </td>
                <td />
              </tr>
            </React.Fragment>
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

PreviousLeaves.propTypes = {
  previousLeaves: PropTypes.array,
  onChange: PropTypes.func,
};

export default PreviousLeaves;
