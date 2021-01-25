import AuthNav from "./AuthNav";
import BetaBanner from "./BetaBanner";
import HeaderSlim from "@massds/mayflower-react/dist/HeaderSlim";
import PropTypes from "prop-types";
import React from "react";
import SiteLogo from "@massds/mayflower-react/dist/SiteLogo";
import User from "../models/User";
import logo from "@massds/mayflower-assets/static/images/logo/stateseal.png";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Global page header, displayed at the top of every page.
 */
const Header = (props) => {
  const { t } = useTranslation();
  const isLoggedIn = props.user;
  const feedbackUrl =
    props.user && props.user.hasEmployerRole
      ? routes.external.massgov.feedbackEmployer
      : routes.external.massgov.feedbackClaimant;

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

  return (
    <React.Fragment>
      {isLoggedIn && <BetaBanner feedbackUrl={feedbackUrl} />}
      <HeaderSlim {...headerProps} />
    </React.Fragment>
  );
};

Header.propTypes = {
  user: PropTypes.instanceOf(User),
  onLogout: PropTypes.func.isRequired,
};

export default Header;
