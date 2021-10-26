import Link from "next/link";
import React from "react";
import classNames from "classnames";

interface Tab {
  label: string;
  href: string;
}

interface NavigationTabsProps {
  activePath: string;
  tabs: Tab[];
}

const NavigationTabs = ({ activePath, tabs }: NavigationTabsProps) => {
  const isActive = (tab: Tab) => tab.href === activePath;

  return (
    <nav className="border-bottom border-base-lighter margin-bottom-5 display-flex width-full">
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
