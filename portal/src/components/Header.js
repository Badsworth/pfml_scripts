import AuthNav from "./AuthNav";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

/**
 * Global page header, displayed at the top of every page.
 */
const Header = (props) => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <a href="#main" className="usa-skipnav">
        {t("components.header.skipToContent")}
      </a>

      <AuthNav user={props.user} />

      <header className="bg-base-lightest">
        <div className="grid-container">
          <div className="grid-row">
            <div className="grid-col-fill margin-left-0 margin-y-3 desktop:margin-y-4">
              <Link href="/">
                <a className="usa-logo__text font-heading-lg text-no-underline text-secondary">
                  {t("components.header.appTitle")}
                </a>
              </Link>
            </div>
          </div>
        </div>
      </header>
    </React.Fragment>
  );
};

Header.propTypes = {
  user: PropTypes.object,
};

export default Header;
