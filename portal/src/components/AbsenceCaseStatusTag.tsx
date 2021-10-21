import { AbsenceCaseStatus } from "../models/Claim";
import React from "react";
import Tag from "./Tag";
import findKeyByValue from "../utils/findKeyByValue";
import formatDate from "../utils/formatDate";
import { isFeatureEnabled } from "../services/featureFlags";
import { orderBy } from "lodash";
import { useTranslation } from "../locales/i18n";

interface AbsenceCaseStatusTagProps {
  status?: string;
  managedRequirements?: Array<{
    follow_up_date: string;
  }>;
}

const AbsenceCaseStatusTag = ({
  status,
  managedRequirements,
}: AbsenceCaseStatusTagProps) => {
  const { t } = useTranslation();
  const mappedStatus = findKeyByValue(AbsenceCaseStatus, status);

  const getTagState = (status) => {
    const successState = ["Approved"];
    const errorState = ["Declined"];
    const inactiveState = ["Closed", "Completed"];

    if (successState.includes(status)) return "success";
    if (errorState.includes(status)) return "error";
    if (inactiveState.includes(status)) return "inactive";
  };

  const findClosestFollowupDate = () => {
    const sortedDates = orderBy(
      managedRequirements,
      [(managedRequirement) => new Date(managedRequirement.follow_up_date)],
      ["asc"]
    );
    return formatDate(sortedDates[0].follow_up_date).short();
  };

  if (managedRequirements?.length > 0) {
    // TODO (EMPLOYER-1542): Remove feature condition
    if (isFeatureEnabled("employerShowReviewByStatus")) {
      return (
        <Tag
          state="warning"
          label={t("components.absenceCaseStatusTag.status_openRequirements", {
            followupDate: findClosestFollowupDate(),
          })}
        />
      );
    }

    // TODO (EMPLOYER-1542): Remove this once Review By feature is always enabled
    return <React.Fragment>--</React.Fragment>;
  }

  // TODO (EMPLOYER-1542): Remove condition
  if (isFeatureEnabled("employerShowReviewByStatus") && !mappedStatus) {
    return (
      <Tag
        state="inactive"
        label={t("components.absenceCaseStatusTag.status_noAction")}
      />
    );
  }

  return mappedStatus ? (
    <Tag
      state={getTagState(status)}
      label={t("components.absenceCaseStatusTag.status", {
        context: mappedStatus,
      })}
    />
  ) : (
    // TODO (EMPLOYER-1542): Replace with `inactive` tag on line 52
    <React.Fragment>--</React.Fragment>
  );
};

export default AbsenceCaseStatusTag;
