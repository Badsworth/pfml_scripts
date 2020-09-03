import AmendLink from "./AmendLink";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display past leaves taken by the employee
 * in the Leave Admin claim review page.
 */

const PastLeave = (props) => {
  const { t } = useTranslation();
  const { previousLeaves } = props;

  return (
    <React.Fragment>
      <ReviewHeading>
        {t("pages.employersClaimsReview.pastLeave.header")}
      </ReviewHeading>
      <Table>
        <thead>
          <tr>
            <th scope="col">
              {t("pages.employersClaimsReview.pastLeave.tableHeader_dateRange")}
            </th>
            <th scope="col" colSpan="2">
              {t("pages.employersClaimsReview.pastLeave.tableHeader_days")}
            </th>
          </tr>
        </thead>
        <tbody>
          {previousLeaves &&
            previousLeaves.map((leavePeriod, index) => {
              return (
                <tr key={index}>
                  <th scope="row">
                    {formatDateRange(
                      leavePeriod.leave_start_date,
                      leavePeriod.leave_end_date
                    )}
                  </th>
                  <td>{t("pages.employersClaimsReview.notApplicable")}</td>
                  <td>
                    <AmendLink />
                  </td>
                </tr>
              );
            })}
          <tr>
            <th scope="row" className="text-bold">
              {t(
                "pages.employersClaimsReview.pastLeave.tableFooter_totalLeave"
              )}
            </th>
            <td colSpan="2">
              {t("pages.employersClaimsReview.notApplicable")}
            </td>
          </tr>
        </tbody>
      </Table>
    </React.Fragment>
  );
};

PastLeave.propTypes = {
  previousLeaves: PropTypes.array,
};

export default PastLeave;
