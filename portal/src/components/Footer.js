import FooterSlim from "@massds/mayflower-react/dist/FooterSlim";
import React from "react";
import SiteLogo from "@massds/mayflower-react/dist/SiteLogo";
import logo from "@massds/mayflower-assets/static/images/logo/stateseal.png";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Global page footer, displayed at the bottom of every page.
 */
const Footer = () => {
  const { t } = useTranslation();

  const footerSlimProps = {
    title: t("components.footer.title"),
    description: t("components.footer.description"),
    contact: {
      address: t("components.footer.orgAddress"),
      phone: t("components.footer.orgPhoneNumber"),
      online: {
        title: t("components.footer.orgName"),
        href: routes.external.massgov.dfml,
      },
    },
    siteLogo: (
      <SiteLogo
        url={{
          domain: routes.home,
        }}
        image={{
          src: logo,
          alt: t("components.siteLogo.alt"),
          width: 45,
          height: 45,
        }}
        title={`${t("components.header.appTitle")} Homepage`}
      />
    ),
  };

  return <FooterSlim {...footerSlimProps} />;
};

export default Footer;
