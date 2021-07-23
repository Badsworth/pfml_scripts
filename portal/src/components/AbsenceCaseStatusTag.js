import { AbsenceCaseStatus } from "../models/Claim";
import PropTypes from "prop-types";
import React from "react";
import Tag from "./Tag";
import findKeyByValue from "../utils/findKeyByValue";
import formatDate from "../utils/formatDate";
import { isFeatureEnabled } from "../services/featureFlags";
import { orderBy } from "lodash";
import { useTranslation } from "../locales/i18n";

const AbsenceCaseStatusTag = ({ status, managedRequirements }) => {
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

  if (
    // TODO (EMPLOYER-1542): Remove feature condition -- Keep managedRequirements check.
    isFeatureEnabled("employerShowReviewByStatus") &&
    managedRequirements?.length > 0
  ) {
    return (
      <Tag
        state="warning"
        label={t("components.absenceCaseStatusTag.status_openRequirements", {
          followupDate: findClosestFollowupDate(),
        })}
      />
    );
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
    "--"
  );
};

AbsenceCaseStatusTag.propTypes = {
  status: PropTypes.string,
  managedRequirements: PropTypes.arrayOf(
    PropTypes.shape({ follow_up_date: PropTypes.string.isRequired })
  ),
};

export default AbsenceCaseStatusTag;
