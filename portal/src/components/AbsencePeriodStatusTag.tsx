import {
  AbsencePeriodRequestDecision,
  AbsencePeriodRequestDecisionEnum,
} from "../models/AbsencePeriod";
import Tag, { TagProps } from "./core/Tag";
import React from "react";
import findKeyByValue from "../utils/findKeyByValue";
import { useTranslation } from "../locales/i18n";

interface AbsencePeriodStatusTagProps {
  className?: string;
  request_decision?: AbsencePeriodRequestDecisionEnum;
}

const StateMap: {
  [status in keyof typeof AbsencePeriodRequestDecision]: TagProps["state"];
} = {
  approved: "success",
  cancelled: "inactive",
  denied: "error",
  inReview: "warning",
  pending: "warning",
  projected: "warning",
  withdrawn: "inactive",
  voided: "inactive",
} as const;

const AbsencePeriodStatusTag = (props: AbsencePeriodStatusTagProps) => {
  const { t } = useTranslation();
  const requestDecisionKey = findKeyByValue(
    AbsencePeriodRequestDecision,
    props.request_decision
  );

  if (!requestDecisionKey) return null;

  return (
    <Tag
      className={props.className}
      label={t("components.absencePeriodStatusTag.label", {
        context: requestDecisionKey,
      })}
      state={StateMap[requestDecisionKey]}
    />
  );
};

export default AbsencePeriodStatusTag;
