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
      control: {
        type: "radio",
        options: TABS.map((tab) => tab.label),
      },
    },
  },
  args: {
    selectedTab: TABS[0].label,
  },
};

export const Default = ({
  selectedTab,
}: {
  selectedTab: typeof TABS[number]["label"];
}) => {
  const activeTab = TABS.find(
    (tab) => tab.label === selectedTab
  ) as typeof TABS[number];

  return <NavigationTabs tabs={TABS} activePath={activeTab.href} />;
};
