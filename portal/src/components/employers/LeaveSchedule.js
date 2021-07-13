import EmployerClaim from "../../models/EmployerClaim";
import IntermittentLeaveSchedule from "./IntermittentLeaveSchedule";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import { Trans } from "react-i18next";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";

/**
 * Display leave periods by leave type
 * in the Leave Admin claim review page.
 */

const LeaveSchedule = ({ hasDocuments, claim }) => {
  const { t } = useTranslation();
  const {
    isContinuous,
    isIntermittent,
    isReducedSchedule,
    leave_details: { intermittent_leave_periods },
  } = claim;

  const buildContext = () => {
    if (isIntermittent && hasDocuments) return "intermittentWithDocuments";
    if (!isIntermittent && hasDocuments) return "documents";
  };

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersLeaveSchedule.header")}
      </ReviewHeading>
      <p>
        <Trans
          i18nKey="components.employersLeaveSchedule.caption"
          tOptions={{
            context: buildContext() || "",
          }}
        />
      </p>
      <Table className="width-full">
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersLeaveSchedule.dateRangeLabel")}
            </th>
            <th scope="col">
              {t("components.employersLeaveSchedule.leaveFrequencyLabel")}
            </th>
            <th scope="col">
              {t("components.employersLeaveSchedule.detailsLabel")}
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
                {t(
                  "components.employersLeaveSchedule.claimDurationType_continuous"
                )}
              </td>
            </tr>
          )}
          {isReducedSchedule && (
            <tr>
              <th scope="row">
                {/* TODO (EMPLOYER-655): Update reduced leave details */}
                {/* {formatDateRange(
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].start_date"
                  ),
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].end_date"
                  )
                )} */}
              </th>
              <td>
                {t(
                  "components.employersLeaveSchedule.claimDurationType_reducedSchedule"
                )}
              </td>
              <td>
                {/* TODO (CP-1074): Update hours/day */}
                {/* TODO (EMPLOYER-655): Update reduced leave details */}
                <Trans
                  i18nKey="components.employersLeaveSchedule.downloadAttachments"
                  components={{
                    "contact-center-phone-link": (
                      <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                    ),
                  }}
                />
                {/* {t(
                  "components.employersLeaveSchedule.reducedHoursPerWeek",
                  {
                    numOfHours: 10,
                  }
                )} */}
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
    </React.Fragment>
  );
};

LeaveSchedule.propTypes = {
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
  hasDocuments: PropTypes.bool,
};

export default LeaveSchedule;
