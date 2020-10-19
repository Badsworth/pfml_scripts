import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import { useTranslation } from "react-i18next";

const StatusTag = ({ state }) => {
  const { t } = useTranslation();
  // TODO (EMPLOYER-421) consider other states.
  const classes = classnames(
    "usa-tag",
    "usa-tag--big",
    "text-bold",
    "padding-x-205",
    "padding-y-05",
    "radius-lg",
    {
      "text-success": state === "approved",
      "bg-success-lighter": state === "approved",
    }
  );

  return (
    <span className={classes}>
      {t("components.tag.state", { context: state })}
    </span>
  );
};

StatusTag.propTypes = {
  // TODO (EMPLOYER-421) consider other states.
  state: PropTypes.oneOf(["approved"]).isRequired,
};

export default StatusTag;
