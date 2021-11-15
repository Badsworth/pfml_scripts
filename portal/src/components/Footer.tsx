import DFMLLogo from "./DFMLLogo.svg";
import FooterSlim from "@massds/mayflower-react/dist/FooterSlim";
import PFMLLogo from "./PFMLLogo.svg";
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
    links: [
      {
        href: routes.external.massgov.privacyPolicy,
        title: t("components.footer.privacyPolicy"),
      },
      {
        href: routes.external.massgov.consentAgreement,
        title: t("components.footer.dataSharingAgreement"),
      },
    ],
    stackedLogo: true,
    siteLogo: (
      <React.Fragment>
        <SiteLogo
          url={{
            domain: routes.external.massgov.dfml,
          }}
          image={{
            src: DFMLLogo,
            alt: t("components.siteLogo.dfmlAlt"),
            width: 165,
            height: 45,
          }}
          title={t("components.footer.logoTitleDFML")}
        />
        <SiteLogo
          url={{
            domain: routes.external.massgov.pfml,
          }}
          image={{
            src: PFMLLogo,
            alt: t("components.siteLogo.pfmlAlt"),
            width: 118,
            height: 45,
          }}
          title={t("components.footer.logoTitlePFML")}
        />
      </React.Fragment>
    ),
  };

  return <FooterSlim {...footerSlimProps} />;
};

export default Footer;
