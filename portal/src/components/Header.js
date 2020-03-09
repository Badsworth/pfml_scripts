import AuthNav from "./AuthNav";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Global page header, displayed at the top of every page.
 */
const Header = props => {
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
              <a
                className="usa-logo__text font-heading-lg text-no-underline text-secondary"
                href="/"
                title="Home"
                aria-label="Home"
              >
                {t("components.header.appTitle")}
              </a>
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
