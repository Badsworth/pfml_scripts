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
        return appLogic.portalFlow.goTo(routes.claims.dashboard);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <React.Fragment>
      <div className="margin-y-3 measure-5">
        <Title>{t("pages.index.employerTitle")}</Title>
      </div>
      <div className="margin-top-6 measure-7">
        <Heading level="2">{t("pages.index.createAccountHeading")}</Heading>

        <div className="grid-row grid-gap">
          <article className="tablet:grid-col margin-bottom-3">
            <div className="bg-base-lightest padding-3">
              <Heading level="3">
                {t("pages.index.employerCreateAccountHeading")}
              </Heading>
              <p>{t("pages.index.employerCreateAccountBody")}</p>
              <ButtonLink
                href={routes.employers.createAccount}
                className="margin-top-3"
              >
                {t("pages.index.createAccountLink")}
              </ButtonLink>
              <div className="margin-top-2 text-base text-bold">
                {t("pages.authCreateAccount.haveAnAccountFooterLabel")}
                <Link href={routes.auth.login}>
                  <a className="display-inline-block margin-left-1">
                    {t("pages.authCreateAccount.logInFooterLink")}
                  </a>
                </Link>
              </div>
            </div>
          </article>
          <article className="tablet:grid-col">
            <div className="bg-base-lightest padding-3">
              <Heading level="3">
                {t("pages.index.claimantCreateAccountHeading")}
              </Heading>
              <p>
                <Trans
                  i18nKey="pages.index.claimantCreateAccountBody"
                  components={{
                    "mass-benefits-timeline-link": (
                      <a
                        href={
                          routes.external.massgov.benefitsTimeline_2020December2
                        }
                      />
                    ),
                  }}
                />
              </p>
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
