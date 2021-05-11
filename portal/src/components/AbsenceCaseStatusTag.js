import { AbsenceCaseStatus } from "../models/Claim";
import PropTypes from "prop-types";
import React from "react";
import Tag from "./Tag";
import findKeyByValue from "../utils/findKeyByValue";
import { useTranslation } from "../locales/i18n";

const AbsenceCaseStatusTag = ({ status }) => {
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

  return status && mappedStatus ? (
    <Tag
      state={getTagState(status)}
      label={t("components.absenceCaseStatusTag.status", {
        context: mappedStatus,
      })}
    />
  ) : (
    "--"
  );
};

AbsenceCaseStatusTag.propTypes = {
  status: PropTypes.string,
};

export default AbsenceCaseStatusTag;
