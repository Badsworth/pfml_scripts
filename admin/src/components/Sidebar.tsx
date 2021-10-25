import Link from "next/link";
import routes from "../routes";
import { useRouter } from "next/router";
import classNames from "classnames";

export default function Sidebar() {
  const router = useRouter();

  return (
    <aside className="page__sidebar" tabIndex={0}>
      <nav className="menu">
        <ul className="menu__list">
          <li className="menu__list-item">
            <Link href={routes.dashboard}>
              <a
                className={classNames("menu__link", "menu__link--dashboard", {
                  "menu__link--active": router.pathname == routes.dashboard,
                })}
                data-testid="dashboard-navigation-link"
              >
                Dashboard
              </a>
            </Link>
          </li>
          <li className="menu__list-item">
            <Link href={routes.users}>
              <a
                className={classNames("menu__link", "menu__link--user-lookup", {
                  "menu__link--active": router.pathname == routes.users,
                })}
                data-testid="users-navigation-link"
              >
                User Lookup
              </a>
            </Link>
          </li>
          <li className="menu__list-item">
            <Link href={routes.maintenance}>
              <a
                className={classNames("menu__link", "menu__link--maintenance", {
                  "menu__link--active": router.pathname == routes.maintenance,
                })}
                data-testid="maintenance-navigation-link"
              >
                Maintenance
              </a>
            </Link>
          </li>
          <li className="menu__list-item">
            <Link href={routes.features}>
              <a
                className={classNames("menu__link", "menu__link--features", {
                  "menu__link--active": router.pathname == routes.features,
                })}
                data-testid="features-navigation-link"
              >
                Features
              </a>
            </Link>
          </li>
        </ul>
      </nav>
      <div className="settings">
        <ul className="settings__list">
          <li className="settings__list-item">
            <Link href={routes.settings}>
              <a
                className={classNames(
                  "settings__link",
                  "settings__link--settings",
                  {
                    "menu__link--active": router.pathname == routes.settings,
                  },
                )}
                data-testid="settings-navigation-link"
              >
                Settings
              </a>
            </Link>
          </li>
          <li className="settings__list-item">
            <Link href={routes.help}>
              <a
                className={classNames(
                  "settings__link",
                  "settings__link--help",
                  {
                    "menu__link--active": router.pathname == routes.help,
                  },
                )}
                data-testid="help-navigation-link"
              >
                Help
              </a>
            </Link>
          </li>
        </ul>
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
