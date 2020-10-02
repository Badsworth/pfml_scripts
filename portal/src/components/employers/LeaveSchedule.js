import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import Table from "../Table";
import { Trans } from "react-i18next";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

// TODO (EMPLOYER-364): Remove hardcoded link
const healthCareProviderCertificationFile = "example-hcp-link.pdf";

/**
 * Display leave periods by leave type
 * in the Leave Admin claim review page.
 */

const LeaveSchedule = (props) => {
  const { t } = useTranslation();
  const {
    isIntermittent,
    leave_details: { intermittent_leave_periods },
  } = props.claim;

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
          {isIntermittent &&
            intermittent_leave_periods.map((leavePeriod) => {
              return (
                <tr key={leavePeriod.leave_period_id} className="intermittent">
                  <th scope="row">
                    {formatDateRange(
                      leavePeriod.start_date,
                      leavePeriod.end_date
                    )}
                  </th>
                  <td>
                    {t(
                      "pages.employersClaimsReview.leaveSchedule.type_intermittent"
                    )}
                  </td>
                  <td>
                    <div>
                      <strong>
                        {t(
                          "pages.employersClaimsReview.leaveSchedule.intermittentDetails_oncePerMonth"
                        )}
                      </strong>
                    </div>
                    <div>
                      <Trans
                        i18nKey="pages.employersClaimsReview.leaveSchedule.intermittentDetails_estimatedAbsences"
                        values={{
                          frequency: leavePeriod.frequency,
                          duration: leavePeriod.duration,
                          durationBasis: leavePeriod.duration_basis.toLowerCase(),
                        }}
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
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
  claim: PropTypes.object,
};

export default LeaveSchedule;
