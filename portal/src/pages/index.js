import React, { useEffect } from "react";
import { Auth } from "@aws-amplify/auth";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import Link from "next/link";
import PropTypes from "prop-types";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export const Index = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  // Redirect logged-in users
  useEffect(() => {
    // eslint-disable-next-line promise/catch-or-return
    Auth.currentUserInfo().then((userInfo) => {
      if (userInfo) {
        return appLogic.portalFlow.goTo(routes.applications.index);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

Index.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default Index;
