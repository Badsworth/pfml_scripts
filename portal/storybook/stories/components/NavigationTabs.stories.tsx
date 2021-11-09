import NavigationTabs from "src/components/NavigationTabs";
import React from "react";
import routes from "src/routes";

const TABS = [
  {
    label: "First",
    href: "/",
  },
  {
    label: "Second",
    href: routes.employers.welcome,
  },
  {
    label: "Third",
    href: routes.employers.organizations,
  },
];

export default {
  title: "Components/NavigationTabs",
  component: NavigationTabs,
  argTypes: {
    selectedTab: {
      defaultValue: TABS[0].label,
      control: {
        type: "radio",
        options: TABS.map((tab) => tab.label),
      },
    },
  },
};

export const Default = ({ selectedTab }: { selectedTab: string }) => {
  const activeTab = TABS.find((tab) => tab.label === selectedTab);
  // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
  return <NavigationTabs tabs={TABS} activePath={activeTab.href} />;
};
