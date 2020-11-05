import EmployerClaim from "../../models/EmployerClaim";
import IntermittentLeaveSchedule from "./IntermittentLeaveSchedule";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import Table from "../Table";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";

// TODO (EMPLOYER-364): Remove hardcoded link
const healthCareProviderCertificationFile = "example-hcp-link.pdf";

/**
 * Display leave periods by leave type
 * in the Leave Admin claim review page.
 */

const LeaveSchedule = ({ claim }) => {
  const { t } = useTranslation();
  const {
    isContinuous,
    isIntermittent,
    isReducedSchedule,
    leave_details: { intermittent_leave_periods },
  } = claim;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("pages.employersClaimsReview.leaveSchedule.header")}
      </ReviewHeading>
      <Table className="width-full">
        <caption>
          {t("pages.employersClaimsReview.leaveSchedule.tableName")}
        </caption>
        <thead>
          <tr>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_dateRange"
              )}
            </th>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_leaveFrequency"
              )}
            </th>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_details"
              )}
            </th>
          </tr>
        </thead>
        <tbody>
          {isContinuous && (
            <tr>
              <th scope="row">
                {formatDateRange(
                  get(
                    claim,
                    "leave_details.continuous_leave_periods[0].start_date"
                  ),
                  get(
                    claim,
                    "leave_details.continuous_leave_periods[0].end_date"
                  )
                )}
              </th>
              <td colSpan="2">
                {t("pages.employersClaimsReview.leaveSchedule.type_continuous")}
              </td>
            </tr>
          )}
          {isReducedSchedule && (
            <tr>
              <th scope="row">
                {formatDateRange(
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].start_date"
                  ),
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].end_date"
                  )
                )}
              </th>
              <td>
                {t(
                  "pages.employersClaimsReview.leaveSchedule.type_reducedSchedule"
                )}
              </td>
              <td>
                {/* TODO (EMPLOYER-364): Remove hardcoded number of hours */}
                {/* TODO (CP-1074): Update hours/day */}
                {t(
                  "pages.employersClaimsReview.leaveSchedule.reducedHoursPerWeek",
                  {
                    numOfHours: 10,
                  }
                )}
              </td>
            </tr>
          )}
          {isIntermittent && (
            <IntermittentLeaveSchedule
              intermittentLeavePeriods={intermittent_leave_periods}
            />
          )}
        </tbody>
      </Table>
      <ReviewRow
        level="3"
        label={t("pages.employersClaimsReview.documentationLabel")}
      >
        <a href={healthCareProviderCertificationFile} className="text-normal">
          {t(
            "pages.employersClaimsReview.leaveSchedule.healthCareProviderFormLink"
          )}
        </a>
      </ReviewRow>
    </React.Fragment>
  );
};

LeaveSchedule.propTypes = {
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
};

export default LeaveSchedule;
