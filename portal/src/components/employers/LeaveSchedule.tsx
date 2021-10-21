import EmployerClaim from "../../models/EmployerClaim";
import IntermittentLeaveSchedule from "./IntermittentLeaveSchedule";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
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
              <td>
                {t(
                  "components.employersLeaveSchedule.claimDurationType_continuous"
                )}
              </td>
              <td></td>
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
                  "components.employersLeaveSchedule.claimDurationType_reducedSchedule"
                )}
              </td>
              <td>
                <Trans
                  i18nKey="components.employersLeaveSchedule.lead"
                  components={{
                    "contact-center-phone-link": (
                      <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                    ),
                  }}
                  tOptions={{
                    context: hasDocuments ? "hasDocs" : "noDocs",
                  }}
                />
              </td>
            </tr>
          )}
          {isIntermittent && (
            <IntermittentLeaveSchedule hasDocuments={hasDocuments} />
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

export default LeaveSchedule;
