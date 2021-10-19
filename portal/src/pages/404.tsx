import ButtonLink from "../components/ButtonLink";
import React from "react";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export default function Custom404() {
  const { t } = useTranslation();
  const exampleRoute = routes.auth.login;
  const exampleUrl =
    typeof window !== "undefined"
      ? `${window.location.protocol}//${window.location.hostname}${exampleRoute}`
      : exampleRoute;

  return (
    <React.Fragment>
      <Title>{t("pages.404.title")}</Title>
      <div className="usa-intro measure-5 margin-bottom-2">
        <Trans
          i18nKey="pages.404.body"
          components={{
            "url-example": <a href={exampleRoute} />,
          }}
          values={{
            url: exampleUrl,
          }}
        />
      </div>

      <ButtonLink href={routes.index}>
        {t("pages.404.homepageButton")}
      </ButtonLink>
    </React.Fragment>
  );
}
