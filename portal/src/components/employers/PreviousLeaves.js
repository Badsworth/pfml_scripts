import Details from "../Details";
import PreviousLeave from "./PreviousLeave";
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
  const { previousLeaves } = props;

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
      </Details>
      <Table className="width-full">
        <thead>
          <tr>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.previousLeaves.tableHeader_dateRange"
              )}
            </th>
            <th scope="col" colSpan="2">
              {t("pages.employersClaimsReview.previousLeaves.tableHeader_days")}
            </th>
          </tr>
        </thead>
        <tbody>
          {previousLeaves.length ? (
            <React.Fragment>
              {previousLeaves.map((leavePeriod) => {
                return (
                  <PreviousLeave
                    leavePeriod={leavePeriod}
                    key={leavePeriod.id}
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
};

export default PreviousLeaves;
