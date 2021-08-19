import Heading from "../../components/Heading";
import React from "react";
import Tag from "../../components/Tag";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import { map } from "lodash";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

const StatusTagMap = {
  Approved: "success",
  Denied: "error",
  Pending: "pending",
  Withdrawn: "inactive",
};

export const LeaveDetails = ({ absenceDetails = {} }) => {
  const { t } = useTranslation();
  return map(absenceDetails, (absenceItem, absenceItemName) => (
    <div
      key={absenceItemName}
      className="border-bottom border-base-lighter margin-bottom-2 padding-bottom-2"
    >
      <Heading level="2">
        {t("pages.claimsStatus.leaveReasonValue", {
          context: absenceItemName,
        })}
      </Heading>
      {absenceItem.length
        ? absenceItem.map(
            ({
              period_type,
              absence_period_start_date,
              absence_period_end_date,
              request_decision,
              fineos_leave_request_id,
            }) => (
              <div key={fineos_leave_request_id} className="margin-top-2">
                <Heading className="margin-bottom-1" level="3">
                  {t("pages.claimsStatus.leavePeriodLabel", {
                    context: period_type.toLowerCase(),
                  })}
                </Heading>
                <p>{`From ${formatDate(
                  absence_period_start_date
                ).full()} to ${formatDate(absence_period_end_date).full()}`}</p>
                <Tag
                  paddingSm
                  label={request_decision}
                  state={StatusTagMap[request_decision]}
                />
                <Trans
                  i18nKey="pages.claimsStatus.leaveStatusMessage"
                  tOptions={{ context: request_decision }}
                  components={{
                    "application-timeline-link": (
                      <a
                        href={
                          routes.external.massgov.applicationApprovalTimeline
                        }
                      />
                    ),
                    "application-link": (
                      <a href={routes.applications.getReady} />
                    ),
                    "request-appeal-link": (
                      <a
                        href={routes.external.massgov.requestAnAppealForPFML}
                      />
                    ),
                  }}
                />
              </div>
            )
          )
        : null}
    </div>
  ));
};

export default LeaveDetails;
