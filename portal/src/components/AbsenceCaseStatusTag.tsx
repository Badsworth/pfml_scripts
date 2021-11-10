import { AbsenceCaseStatus } from "../models/Claim";
import React from "react";
import Tag from "./core/Tag";
import findKeyByValue from "../utils/findKeyByValue";
import formatDate from "../utils/formatDate";
import { orderBy } from "lodash";
import { useTranslation } from "../locales/i18n";

interface AbsenceCaseStatusTagProps {
  status?: string | null;
  managedRequirements?: Array<{
    follow_up_date: string | null;
  }>;
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

  const findClosestFollowupDate = () => {
    const managedRequirementsWithFollowUpDate = managedRequirements?.filter(
      (requirement) => requirement.follow_up_date
    );
    const sortedDates = orderBy(
      managedRequirementsWithFollowUpDate,
      [
        (managedRequirement) =>
          new Date(managedRequirement.follow_up_date as string),
      ],
      ["asc"]
    );
    return formatDate(sortedDates[0].follow_up_date).short();
  };

  if (managedRequirements && managedRequirements.length > 0) {
    return (
      <Tag
        state="warning"
        label={t("components.absenceCaseStatusTag.status_openRequirements", {
          followupDate: findClosestFollowupDate(),
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
