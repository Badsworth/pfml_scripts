import Logo from "@massds/mayflower-react/dist/SiteLogo";
import React from "react";
import logo from "@massds/mayflower-assets/static/images/stateseal.png";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Site-wide logo, displayed in the footer.
 * Mayflower component: https://mayflower.digital.mass.gov/react/index.html?path=/story/atoms-media--sitelogo
 */
const SiteLogo = () => {
  const { t } = useTranslation();

  const siteLogoProps = {
    url: {
      domain: routes.home,
    },
    image: {
      src: logo,
      alt: t("components.siteLogo.alt"),
      width: 45,
      height: 45,
    },
    siteName: t("pages.app.siteTitle"),
  };
  return <Logo {...siteLogoProps} />;
};

export default SiteLogo;
