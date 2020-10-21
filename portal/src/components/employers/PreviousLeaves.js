import AmendablePreviousLeave from "./AmendablePreviousLeave";
import Details from "../Details";
import PreviousLeave from "../../models/PreviousLeave";
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
                    key={leavePeriod.id}
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
    </React.Fragment>
  );
};

PreviousLeaves.propTypes = {
  previousLeaves: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave)),
  onChange: PropTypes.func.isRequired,
};

export default PreviousLeaves;
