import { AbsenceCaseStatus, ManagedRequirement } from "../models/Claim";
import React from "react";
import Tag from "./core/Tag";
import findKeyByValue from "../utils/findKeyByValue";
import getClosestOpenFollowUpDate from "../utils/getClosestOpenFollowUpDate";
import { useTranslation } from "../locales/i18n";

interface AbsenceCaseStatusTagProps {
  status?: string | null;
  managedRequirements?: ManagedRequirement[];
}

const AbsenceCaseStatusTag = ({
  status,
  managedRequirements,
}: AbsenceCaseStatusTagProps) => {
  const { t } = useTranslation();
  const mappedStatus = findKeyByValue(AbsenceCaseStatus, status);

  const getTagState = (status?: string | null) => {
    const successState = ["Approved"];
    const errorState = ["Declined"];
    const inactiveState = ["Closed", "Completed"];

    if (status) {
      if (successState.includes(status)) return "success";
      if (errorState.includes(status)) return "error";
      if (inactiveState.includes(status)) return "inactive";
    }
    return "pending";
  };

  const hasOpenManagedRequirement = managedRequirements?.some((requirement) => {
    return requirement.status === "Open";
  });

  if (managedRequirements && hasOpenManagedRequirement) {
    return (
      <Tag
        state="warning"
        label={t("components.absenceCaseStatusTag.status_openRequirements", {
          followupDate: getClosestOpenFollowUpDate(managedRequirements),
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
