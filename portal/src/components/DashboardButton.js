import ButtonLink from "./ButtonLink";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

/**
 * Link styled as a button that takes the user to the dashboard.
 */
const DashboardButton = ({ variation }) => {
  const { t } = useTranslation();

  const props = Object.assign({
    children: t("components.dashboardButton.text"),
    href: "/",
    variation,
  });

  return <ButtonLink {...props} />;
};

DashboardButton.propTypes = {
  /**
   * If present, determines button style variation.
   */
  variation: PropTypes.oneOf(["outline"]),
};

export default DashboardButton;
