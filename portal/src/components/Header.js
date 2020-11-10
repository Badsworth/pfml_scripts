import AuthNav from "./AuthNav";
import HeaderSlim from "@massds/mayflower-react/dist/HeaderSlim";
import PropTypes from "prop-types";
import React from "react";
import SiteLogo from "@massds/mayflower-react/dist/SiteLogo";
import logo from "@massds/mayflower-assets/static/images/logo/stateseal.png";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Global page header, displayed at the top of every page.
 */
const Header = (props) => {
  const { t } = useTranslation();

  const headerProps = {
    siteLogo: (
      <SiteLogo
        url={{
          domain: routes.index,
        }}
        image={{
          src: logo,
          alt: t("components.siteLogo.sealAlt"),
          width: 45,
          height: 45,
        }}
        siteName={t("components.header.appTitle")}
      />
    ),
    skipNav: (
      <a href="#main" className="usa-skipnav">
        {t("components.header.skipToContent")}
      </a>
    ),
    utilityNav: <AuthNav user={props.user} onLogout={props.onLogout} />,
  };

  return <HeaderSlim {...headerProps} />;
};

Header.propTypes = {
  user: PropTypes.object,
  onLogout: PropTypes.func.isRequired,
};

export default Header;
