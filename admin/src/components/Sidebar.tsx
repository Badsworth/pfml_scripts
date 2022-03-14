import * as api from "../api";
import * as heroIcons from "@heroicons/react/solid";

import menus, { Menu } from "../menus";

import Link from "next/link";
import React from "react";
import WithPermissions from "./WithPermissions";
import classNames from "classnames";
import routes from "../routes";
import { useRouter } from "next/router";

type Props = {
  user: api.AdminUserResponse;
};

type RouteMenu = [string, Menu];

export default function Sidebar({ user }: Props) {
  const router = useRouter();

  function getMenus(isMainMenu: boolean) {
    const sidebarMenus = Object.entries(menus);
    return sidebarMenus
      .reduce((allMenus, [page, menu]: RouteMenu) => {
        const menuFilter = isMainMenu ? menu.isMainMenu : menu.isSettings;
        if (menuFilter) {
          allMenus.push([page, menu]);
        }
        return allMenus;
      }, [] as RouteMenu[])
      .map(([page, menu]: [string, Menu]) => {
        const Icon =
          menu?.heroIconName &&
          heroIcons[menu.heroIconName as keyof typeof heroIcons];
        const menuName = isMainMenu ? "menu" : "settings";
        const MenuItem = (
          <li className={`${menuName}__list-item`}>
            <Link href={routes[page]}>
              <a
                className={classNames(
                  `${menuName}__link`,
                  `${menuName}__link--${page}`,
                  {
                    [`${menuName}__link--active`]:
                      router.pathname == routes[page],
                  },
                )}
                data-testid={`${page}-navigation-link`}
              >
                {Icon && (
                  <Icon
                    className={`${menuName}__link-icon ${menuName}__link-icon--${page}`}
                  />
                )}
                <span>{menu.title}</span>
              </a>
            </Link>
          </li>
        );
        return (
          <React.Fragment key={page}>
            {menu.permissions.length > 0 ? (
              <WithPermissions user={user} permissions={menu.permissions}>
                {MenuItem}
              </WithPermissions>
            ) : (
              MenuItem
            )}
          </React.Fragment>
        );
      });
  }

  return (
    <aside className="page__sidebar" tabIndex={0}>
      <nav className="menu">
        <ul className="menu__list">{getMenus(true)}</ul>
      </nav>
      <div className="settings">
        <ul className="settings__list">{getMenus(false)}</ul>
      </div>
      <div className="environment">
        <div className="environment__label">Environment</div>
        <div className="environment__flag" data-testid="environment-flag">
          Production
        </div>
      </div>
    </aside>
  );
}
