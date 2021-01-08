import React, { useEffect } from "react";
import { Auth } from "@aws-amplify/auth";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import Link from "next/link";
import PropTypes from "prop-types";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export const Index = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const showSelfRegistration = isFeatureEnabled(
    "employerShowSelfRegistrationForm"
  );

  // Redirect logged-in users
  useEffect(() => {
    // eslint-disable-next-line promise/catch-or-return
    Auth.currentUserInfo().then((userInfo) => {
      if (userInfo) {
        return appLogic.portalFlow.goTo(routes.applications.dashboard);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <React.Fragment>
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
      <div className="margin-top-6 measure-7">
        <Heading level="2">{t("pages.index.createAccountHeading")}</Heading>

        <div className="grid-row grid-gap">
          <article className="margin-bottom-3 measure-3">
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
          {!showSelfRegistration && (
            <article className="measure-3">
              <div className="bg-base-lightest padding-3">
                <Heading level="3">{t("pages.index.employerHeading")}</Heading>
                <p>
                  {t("pages.index.employerCardBody_massEmployer")}
                  <br />
                  <Trans
                    i18nKey="pages.index.employerCardBody_contactCenter"
                    components={{
                      "contact-center-phone-link": (
                        <a
                          href={`tel:${t("shared.contactCenterPhoneNumber")}`}
                        />
                      ),
                    }}
                  />
                </p>
              </div>
            </article>
          )}
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
