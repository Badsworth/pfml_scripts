import Link from "next/link";
import routes from "../routes";

export default function Sidebar() {
  return (
    <aside className="page__sidebar" tabIndex={0}>
      <nav className="menu">
        <ul className="menu__list">
          <li className="menu__list-item">
            <Link href="/dashboard">
              <a className="menu__link menu__link--dashboard">Dashboard</a>
            </Link>
          </li>
          <li className="menu__list-item">
            <Link href="/users">
              <a className="menu__link menu__link--user-lookup">User Lookup</a>
            </Link>
          </li>
          <li className="menu__list-item">
            <a href="#" className="menu__link menu__link--maintenance">
              Maintenance
            </a>
          </li>
          <li className="menu__list-item">
            <Link href="/features">
              <a className="menu__link menu__link--features">Features</a>
            </Link>
          </li>
        </ul>
      </nav>
      <div className="settings">
        <ul className="settings__list">
          <li className="settings__list-item">
            <a href="#" className="settings__link settings__link--settings">
              Settings
            </a>
          </li>
          <li className="settings__list-item">
            <a href="#" className="settings__link settings__link--help">
              Help
            </a>
          </li>
        </ul>
      </div>
      <div className="environment">
        <div className="environment__label">Environment</div>
        <div className="environment__flag">Production</div>
      </div>
    </aside>
  );
}
