import FooterSlim from "@massds/mayflower-react/dist/FooterSlim";
import React from "react";
import SiteLogo from "./SiteLogo";
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
    siteLogo: <SiteLogo />,
  };

  return <FooterSlim {...footerSlimProps} />;
};

export default Footer;
