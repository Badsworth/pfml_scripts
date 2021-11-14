import React, { useEffect } from "react";
import ButtonLink from "./ButtonLink";
import Title from "./core/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import tracker from "../services/tracker";
import { useTranslation } from "../locales/i18n";

export default function PageNotFound() {
  const { t } = useTranslation();
  const exampleRoute = routes.auth.login;
  const exampleUrl =
    typeof window !== "undefined"
      ? `${window.location.protocol}//${window.location.hostname}${exampleRoute}`
      : exampleRoute;

  useEffect(() => {
    tracker.trackEvent("Page not found");
  }, []);

  return (
    <React.Fragment>
      <Title>{t("components.pageNotFound.title")}</Title>
      <div className="usa-intro measure-5 margin-bottom-2">
        <Trans
          i18nKey="components.pageNotFound.body"
          components={{
            "url-example": <a href={exampleRoute} />,
          }}
          values={{
            url: exampleUrl,
          }}
        />
      </div>

      <ButtonLink href={routes.index}>
        {t("components.pageNotFound.homepageButton")}
      </ButtonLink>
    </React.Fragment>
  );
}
