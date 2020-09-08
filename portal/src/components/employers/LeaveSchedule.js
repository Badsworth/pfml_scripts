import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import Table from "../Table";
import { Trans } from "react-i18next";
import { useTranslation } from "../../locales/i18n";

const healthCareProviderCertificationFile = "example-hcp-link.pdf";

/**
 * Display leave periods by leave type
 * in the Leave Admin claim review page.
 */

const LeaveSchedule = (props) => {
  const { t } = useTranslation();
  const {
    isContinuous,
    isIntermittent,
    isReducedSchedule,
    temp: {
      leave_details: {
        continuous_leave_periods,
        reduced_schedule_leave_periods,
      },
    },
    leave_details: { intermittent_leave_periods },
  } = props.claim;

  return (
    <React.Fragment>
      <ReviewHeading>
        {t("pages.employersClaimsReview.leaveSchedule.header")}
      </ReviewHeading>
      <Table>
        <caption>
          {t("pages.employersClaimsReview.leaveSchedule.tableName")}
        </caption>
        <thead>
          <tr>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_duration"
              )}
            </th>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_frequency"
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
          {isContinuous &&
            continuous_leave_periods.map((leavePeriod) => {
              return (
                <tr key={leavePeriod.leave_period_id} className="continuous">
                  <th scope="row">
                    {t("pages.employersClaimsReview.durationBasis_weeks", {
                      numOfWeeks: leavePeriod.weeks,
                    })}
                  </th>
                  <td>
                    {t(
                      "pages.employersClaimsReview.leaveSchedule.type_continuous"
                    )}
                  </td>
                  <td />
                </tr>
              );
            })}
          {isReducedSchedule &&
            reduced_schedule_leave_periods.map((leavePeriod) => {
              return (
                <tr key={leavePeriod.leave_period_id} className="reduced">
                  <th scope="row">
                    {t("pages.employersClaimsReview.durationBasis_weeks", {
                      numOfWeeks: leavePeriod.weeks,
                    })}
                  </th>
                  <td>
                    {t(
                      "pages.employersClaimsReview.leaveSchedule.type_reducedSchedule"
                    )}
                  </td>
                  <td>
                    {t(
                      "pages.employersClaimsReview.leaveSchedule.reducedDetails_reducedHours"
                    )}
                  </td>
                </tr>
              );
            })}
          {isIntermittent &&
            intermittent_leave_periods.map((leavePeriod) => {
              return (
                <tr key={leavePeriod.leave_period_id} className="intermittent">
                  <th scope="row">
                    {t("pages.employersClaimsReview.notApplicable")}
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
                        components={{
                          emphasized: <strong />,
                        }}
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
      <ReviewRow label={t("pages.employersClaimsReview.documentationLabel")}>
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
