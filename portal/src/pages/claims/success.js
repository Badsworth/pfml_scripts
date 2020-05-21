import ButtonLink from "../../components/ButtonLink";
import Lead from "../../components/Lead";
import React from "react";
import Title from "../../components/Title";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

/**
 * Success page, shown when an application is successfully submitted.
 */
const Success = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Title>{t("pages.claimsSuccess.title")}</Title>
      <Lead>{t("pages.claimsSuccess.body")}</Lead>
      <ButtonLink href={routes.home}>
        {t("pages.claimsSuccess.dashboardLink")}
      </ButtonLink>
    </React.Fragment>
  );
};

export default Success;
