import {
  ManagedRequirement,
  getSoonestReviewableFollowUpDate,
} from "../models/ManagedRequirement";
import { AbsenceCaseStatus } from "../models/Claim";
import React from "react";
import Tag from "./core/Tag";
import findKeyByValue from "../utils/findKeyByValue";
import { useTranslation } from "../locales/i18n";

interface AbsenceCaseStatusTagProps {
  status?: string | null;
  managedRequirements: ManagedRequirement[];
}

const AbsenceCaseStatusTag = ({
  status,
  managedRequirements,
}: AbsenceCaseStatusTagProps) => {
  const { t } = useTranslation();
  const mappedStatus = findKeyByValue(AbsenceCaseStatus, status);
  const closestReviewableFollowUpDate =
    getSoonestReviewableFollowUpDate(managedRequirements);

  const getTagState = (status?: string | null) => {
    const successState = ["Approved"];
    const errorState = ["Declined"];
    const inactiveState = ["Closed", "Completed"];

    if (status) {
      if (successState.includes(status)) return "success";
      if (errorState.includes(status)) return "error";
      if (inactiveState.includes(status)) return "inactive";
    }
    return "warning";
  };

  if (closestReviewableFollowUpDate) {
    return (
      <Tag
        state="warning"
        label={t("components.absenceCaseStatusTag.status_openRequirements", {
          followupDate: closestReviewableFollowUpDate,
        })}
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
    <Tag
      state="inactive"
      label={t("components.absenceCaseStatusTag.status_noAction")}
    />
  );
};

export default AbsenceCaseStatusTag;
