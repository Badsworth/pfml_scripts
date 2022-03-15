import NavigationTabs from "./NavigationTabs";
import React from "react";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface EmployerNavigationTabsProps {
  activePath: string;
}

const EmployerNavigationTabs = ({
  activePath,
}: EmployerNavigationTabsProps) => {
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

  return (
    <NavigationTabs
      aria-label={t("components.employersNavigationTabs.label")}
      tabs={tabs}
      activePath={activePath}
    />
  );
};

export default EmployerNavigationTabs;
