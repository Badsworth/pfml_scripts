import { AppLogic } from "../hooks/useAppLogic";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/core/Heading";
import Link from "next/link";
import React from "react";
import Title from "../components/core/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import useLoggedInRedirect from "../hooks/useLoggedInRedirect";
import { useTranslation } from "../locales/i18n";

interface IndexProps {
  appLogic: AppLogic;
}

export const Index = (props: IndexProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  useLoggedInRedirect(appLogic.portalFlow, routes.applications.index);

  return (
    <React.Fragment>
      <div className="maxw-desktop">
        <Title seoTitle={t("pages.index.seoTitle")}>
          <Trans
            i18nKey="pages.index.title"
            components={{
              "mass-paid-leave-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.paidLeave}
                />
              ),
            }}
          />
        </Title>
      </div>
      <div className="margin-top-6 measure-7">
        <Heading level="2">{t("pages.index.createAccountHeading")}</Heading>
        <p>{t("pages.index.createAccountHint")}</p>

        <div className="grid-row grid-gap">
          <article className="grid-col-12 mobile-lg:grid-col margin-bottom-3">
            <div className="bg-base-lightest padding-3">
              <Heading level="3">{t("pages.index.claimantHeading")}</Heading>
              <p>{t("pages.index.claimantCardBody")}</p>
              <ButtonLink
                href={routes.auth.createAccount}
                className="margin-top-3"
              >
                {t("pages.index.claimantCreateAccountButton")}
              </ButtonLink>
              <div className="margin-top-2 text-dark text-bold">
                {t("pages.authCreateAccount.haveAnAccountFooterLabel")}
                <Link href={routes.auth.login}>
                  <a className="display-inline-block margin-left-1">
                    {t("pages.authCreateAccount.logInFooterLink")}
                  </a>
                </Link>
              </div>
            </div>
          </article>
          <article className="grid-col-12 mobile-lg:grid-col">
            <div className="bg-base-lightest padding-3">
              <Heading level="3">{t("pages.index.employerHeading")}</Heading>
              <p>{t("pages.index.employerCardBody")}</p>
              <ButtonLink
                href={routes.employers.createAccount}
                className="margin-top-3"
              >
                {t("pages.index.employerCreateAccountButton")}
              </ButtonLink>
              <div className="margin-top-2 text-dark text-bold">
                {t("pages.authCreateAccount.haveAnAccountFooterLabel")}
                <Link href={routes.auth.login}>
                  <a className="display-inline-block margin-left-1">
                    {t("pages.authCreateAccount.logInFooterLink")}
                  </a>
                </Link>
              </div>
            </div>
          </article>
        </div>
      </div>
    </React.Fragment>
  );
};

export default Index;
