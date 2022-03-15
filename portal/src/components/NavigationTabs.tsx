import Link from "next/link";
import React from "react";
import classNames from "classnames";

interface Tab {
  label: string;
  href: string;
}

interface NavigationTabsProps {
  activePath: string;
  "aria-label"?: string;
  // prop to determine if queries are ignored during the isActive match function
  ignoreQueries?: boolean;
  marginBottom?: "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8";
  tabs: Tab[];
}

const NavigationTabs = (props: NavigationTabsProps) => {
  const { activePath, ignoreQueries, marginBottom = "5", tabs } = props;
  const isActive = (tab: Tab) =>
    ignoreQueries
      ? tab.href.split("?")[0] === activePath
      : tab.href === activePath;

  return (
    <nav
      aria-label={props["aria-label"]}
      className={`border-bottom border-base-lighter margin-bottom-${marginBottom} display-flex width-full`}
    >
      {tabs.map((tab) => (
        <Link key={tab.href} href={tab.href}>
          <a
            aria-current={isActive(tab) ? "page" : undefined}
            className={classNames(
              "display-inline-block padding-y-2 margin-bottom-neg-1px text-no-underline width-card",
              {
                // inactive page link
                "text-base-dark hover:text-primary hover:text-underline":
                  !isActive(tab),
                // active page link
                "border-primary border-bottom-05 text-bold text-primary":
                  isActive(tab),
              }
            )}
          >
            {tab.label}
          </a>
        </Link>
      ))}
    </nav>
  );
};

export default NavigationTabs;
