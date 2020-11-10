import FooterSlim from "@massds/mayflower-react/dist/FooterSlim";
import React from "react";
import SiteLogo from "@massds/mayflower-react/dist/SiteLogo";
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
    stackedLogo: true,
    siteLogo: (
      <React.Fragment>
        <SiteLogo
          url={{
            domain: routes.index,
          }}
          image={{
            src: "/DFML_logo_RGB_Gray.svg",
            alt: t("components.siteLogo.dfmlAlt"),
            width: 165,
            height: 45,
          }}
          title={t("components.footer.logoTitle")}
        />
        <SiteLogo
          url={{
            domain: routes.index,
          }}
          image={{
            src: "/PFML_logo_RGB_Gray.svg",
            alt: t("components.siteLogo.pfmlAlt"),
            width: 118,
            height: 45,
          }}
          title={t("components.footer.logoTitle")}
        />
      </React.Fragment>
    ),
  };

  return <FooterSlim {...footerSlimProps} />;
};

export default Footer;
