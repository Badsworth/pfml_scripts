import EmployerClaim from "../../models/EmployerClaim";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../core/Table";
import { Trans } from "react-i18next";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";

interface LeaveScheduleProps {
  claim: EmployerClaim;
  hasDocuments?: boolean;
}

/**
 * Display leave periods by leave type
 * in the Leave Admin claim review page.
 */
const LeaveSchedule = ({ hasDocuments, claim }: LeaveScheduleProps) => {
  const { t } = useTranslation();
  const { isContinuous, isIntermittent, isReducedSchedule } = claim;

  const buildContext = () => {
    if (isIntermittent && hasDocuments) return "intermittentWithDocuments";
    if (!isIntermittent && hasDocuments) return "documents";
  };

  const tableHeadings = [
    t("components.employersLeaveSchedule.dateRangeLabel"),
    t("components.employersLeaveSchedule.leaveFrequencyLabel"),
  ];

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
      <Table className="width-full" responsive>
        <thead>
          <tr>
            {tableHeadings.map((heading) => (
              <th key={heading} scope="col">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isContinuous && (
            <tr>
              <th scope="row" data-label={tableHeadings[0]}>
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
              <td data-label={tableHeadings[1]}>
                {t(
                  "components.employersLeaveSchedule.claimDurationType_continuous"
                )}
              </td>
            </tr>
          )}
          {isReducedSchedule && (
            <tr>
              <th scope="row" data-label={tableHeadings[0]}>
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
              <td data-label={tableHeadings[1]}>
                {t(
                  "components.employersLeaveSchedule.claimDurationType_reducedSchedule"
                )}
              </td>
            </tr>
          )}
          {isIntermittent && (
            <tr>
              <th scope="row" data-label={tableHeadings[0]}>
                {formatDateRange(
                  claim.leave_details.intermittent_leave_periods[0].start_date,
                  claim.leave_details.intermittent_leave_periods[0].end_date
                )}
              </th>
              <td data-label={tableHeadings[1]}>
                {t(
                  "components.employersLeaveSchedule.claimDurationType_intermittent"
                )}
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

export default LeaveSchedule;
