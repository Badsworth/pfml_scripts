import AuthNav from "./AuthNav";
import HeaderSlim from "@massds/mayflower-react/dist/HeaderSlim";
import PropTypes from "prop-types";
import React from "react";
import SiteLogo from "@massds/mayflower-react/dist/SiteLogo";
import { Trans } from "react-i18next";
import logo from "@massds/mayflower-assets/static/images/logo/stateseal.png";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Global page header, displayed at the top of every page.
 */
const Header = (props) => {
  const { t } = useTranslation();
  const isLoggedIn = props.user;
  const feedbackLink =
    isLoggedIn && props.user.hasEmployerRole
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

  const betaBanner = (
    <div className="bg-base-lightest">
      <div className="c-beta-banner">
        <span className="display-inline-block bg-secondary margin-right-1 padding-x-2 text-bold text-white">
          {t("pages.app.betaBannerTag")}
        </span>
        <Trans
          i18nKey="pages.app.betaBannerText"
          components={{
            "user-feedback-link": (
              <a target="_blank" rel="noopener" href={feedbackLink} />
            ),
          }}
        />
      </div>
    </div>
  );
  return (
    <React.Fragment>
      {isLoggedIn && betaBanner}
      <HeaderSlim {...headerProps} />
    </React.Fragment>
  );
};

Header.propTypes = {
  user: PropTypes.object,
  onLogout: PropTypes.func.isRequired,
};

export default Header;
