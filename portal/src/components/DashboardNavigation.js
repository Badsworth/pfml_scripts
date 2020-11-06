import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Tab link navigation bar used on the dashboard
 */
function DashboardNavigation(props) {
  const { t } = useTranslation();

  const links = [
    {
      href: routes.claims.dashboard,
      label: t("components.dashboardNavigation.createApplicationLink"),
    },
    {
      href: routes.applications,
      label: t("components.dashboardNavigation.applicationsLink"),
    },
  ];

  /**
   * Check if a link is the active page
   * @param {{ href: string }} link
   * @returns {boolean}
   */
  const isActive = (link) => props.activeHref === link.href;

  return (
    <nav className="border-bottom border-base-lighter margin-bottom-5 display-flex">
      {links.map((link, index) => (
        <Link key={link.href} href={link.href}>
          <a
            aria-current={isActive(link) ? "page" : undefined}
            className={classnames(
              "display-inline-block padding-y-2 margin-bottom-neg-1px text-no-underline",
              {
                // inactive page link
                "text-base-dark hover:text-primary hover:text-underline": !isActive(
                  link
                ),
                // active page link:
                "border-primary border-bottom-05 text-bold text-primary": isActive(
                  link
                ),
                // exclude right margin on last link
                "margin-right-4": index < links.length - 1,
              }
            )}
          >
            {link.label}
          </a>
        </Link>
      ))}
    </nav>
  );
}

DashboardNavigation.propTypes = {
  /** Route of the active page */
  activeHref: PropTypes.string,
};

export default DashboardNavigation;
