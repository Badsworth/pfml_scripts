import AlertBar from "./core/AlertBar";
import AuthNav from "./AuthNav";
import BetaBanner from "./BetaBanner";
import HeaderSlim from "@massds/mayflower-react/dist/HeaderSlim";
import React from "react";
import SiteLogo from "@massds/mayflower-react/dist/SiteLogo";
import { Trans } from "react-i18next";
import User from "../models/User";
import logo from "@massds/mayflower-assets/static/images/logo/stateseal.png";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface HeaderProps {
  user?: User;
  onLogout: React.MouseEventHandler<HTMLButtonElement>;
  showUpcomingMaintenanceAlertBar: boolean;
  maintenanceStartTime: string | null;
  maintenanceEndTime: string | null;
}

/**
 * Global page header, displayed at the top of every page.
 */
const Header = (props: HeaderProps) => {
  const { t } = useTranslation();
  const isLoggedIn = props.user;
  const feedbackUrl =
    props.user && props.user.hasEmployerRole
      ? routes.external.massgov.feedbackEmployer
      : routes.external.massgov.feedbackClaimant;

  const {
    showUpcomingMaintenanceAlertBar,
    maintenanceStartTime,
    maintenanceEndTime,
  } = props;

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
    utilityNav: <AuthNav user={props.user} onLogout={props.onLogout} />,
  };

  return (
    <React.Fragment>
      <a href="#main" className="usa-skipnav">
        {t("components.header.skipToContent")}
      </a>
      {showUpcomingMaintenanceAlertBar && maintenanceStartTime && (
        <AlertBar>
          <Trans
            i18nKey="components.maintenanceAlertBar.message"
            tOptions={{ context: maintenanceEndTime ? "withEndTime" : null }}
            values={{
              start: maintenanceStartTime,
              end: maintenanceEndTime,
            }}
          />
        </AlertBar>
      )}
      {isLoggedIn && <BetaBanner feedbackUrl={feedbackUrl} />}
      <HeaderSlim {...headerProps} />
    </React.Fragment>
  );
};

export default Header;
