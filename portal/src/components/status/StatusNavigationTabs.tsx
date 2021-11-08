import NavigationTabs from "../NavigationTabs";
import React from "react";
import { createRouteWithQuery } from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface StatusNavigationTabsProps {
  activePath: string;
  absence_case_id?: string | null;
}

/**
 * Navigation tabs to be used on the Claimant Status Page
 */
const StatusNavigationTabs = ({
  activePath,
  absence_case_id,
}: StatusNavigationTabsProps) => {
  const { t } = useTranslation();
  const tabs = [
    {
      label: t("components.statusNavigationTabs.statusDetails"),
      href: createRouteWithQuery(routes.applications.status.claim, {
        absence_case_id,
      }),
    },
    {
      label: t("components.statusNavigationTabs.payments"),
      href: createRouteWithQuery(routes.applications.status.payments, {
        absence_case_id,
      }),
    },
  ];

  return (
    <NavigationTabs
      marginBottom="0"
      ignoreQueries
      tabs={tabs}
      activePath={activePath}
    />
  );
};

export default StatusNavigationTabs;
