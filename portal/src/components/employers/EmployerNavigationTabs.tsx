import NavigationTabs from "../NavigationTabs";
import PropTypes from "prop-types";
import React from "react";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

const EmployerNavigationTabs = ({ activePath }) => {
  const { t } = useTranslation();
  const tabs = [
    {
      label: t("components.employersNavigationTabs.welcome"),
      href: routes.employers.welcome,
    },
    {
      label: t("components.employersNavigationTabs.dashboard"),
      href: routes.employers.dashboard,
    },
  ];

  return <NavigationTabs tabs={tabs} activePath={activePath} />;
};

EmployerNavigationTabs.propTypes = {
  activePath: PropTypes.string.isRequired,
};

export default EmployerNavigationTabs;
