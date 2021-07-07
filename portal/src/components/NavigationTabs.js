import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

const NavigationTabs = ({ activePath, tabs }) => {
  const isActive = (tab) => tab.href === activePath;

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

NavigationTabs.propTypes = {
  activePath: PropTypes.string.isRequired,
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      href: PropTypes.string.isRequired,
    })
  ).isRequired,
};

export default NavigationTabs;
