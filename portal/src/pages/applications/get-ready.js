import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import Alert from "../../components/Alert";
import ButtonLink from "../../components/ButtonLink";
import ClaimCollection from "../../models/ClaimCollection";
import Heading from "../../components/Heading";
import Icon from "../../components/Icon";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaims from "../../hoc/withClaims";

export const GetReady = (props) => {
  const { appLogic, claims } = props;
  const { t } = useTranslation();

  const hasClaims = !claims.isEmpty;

  const iconClassName =
    "margin-right-1 text-secondary text-middle margin-top-neg-05";

  const alertIconProps = {
    className: iconClassName,
    height: 20,
    width: 20,
    fill: "currentColor",
  };

  return (
    <React.Fragment>
      {hasClaims && (
        <Link href={appLogic.portalFlow.getNextPageRoute("SHOW_APPLICATIONS")}>
          <a className="display-inline-block margin-bottom-5">
            {t("pages.getReady.applicationsLink")}
          </a>
        </Link>
      )}

      <Title>{t("pages.getReady.title")}</Title>

      <Alert
        heading={t("pages.getReady.alertHeading")}
        state="info"
        neutral
        className="margin-bottom-3"
      >
        <Heading level="3" className="margin-top-3">
          <IconLaptop {...alertIconProps} />
          {t("pages.getReady.alertOnlineHeading")}
        </Heading>

        <Trans
          i18nKey="pages.getReady.alertOnline"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <Heading level="3">
          <IconPhone {...alertIconProps} />
          {t("pages.getReady.alertPhoneHeading")}
        </Heading>

        <Trans
          i18nKey="pages.getReady.alertPhone"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            "benefits-timeline-link": (
              <a
                href={routes.external.massgov.benefitsTimeline_2020December2}
              />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />
      </Alert>

      <div className="measure-6">
        <Heading level="2">
          <Icon className={iconClassName} name="comment" />
          {t("pages.getReady.stepOneHeading")}
        </Heading>
        <Trans i18nKey="pages.getReady.stepOne" />

        <Heading level="2">
          <Icon className={iconClassName} name="upload_file" />
          {t("pages.getReady.stepTwoHeading")}
        </Heading>
        <Trans
          i18nKey="pages.getReady.stepTwo"
          components={{
            "healthcare-provider-form-link": (
              <a href={routes.external.massgov.healthcareProviderForm} />
            ),
          }}
        />

        <Heading level="2">
          <Icon className={iconClassName} name="edit" />
          {t("pages.getReady.stepThreeHeading")}
        </Heading>
        <Trans
          i18nKey="pages.getReady.stepThree"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            "medical-bonding-link": (
              <a href={routes.external.massgov.medicalBonding} />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
            "tax-liability-link": (
              <a href={routes.external.massgov.taxLiability} />
            ),
          }}
        />
        <ButtonLink
          className="margin-top-3 margin-bottom-8"
          href={appLogic.portalFlow.getNextPageRoute("START_APPLICATION")}
        >
          {t("pages.getReady.createClaimButton")}
        </ButtonLink>

        <ButtonLink
          className="margin-top-3 margin-bottom-8"
          href={appLogic.portalFlow.getNextPageRoute("LINK_APPLICATION")}
        >
          {t("pages.getReady.linkClaimButton")}
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

GetReady.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }),
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
};

export default withClaims(GetReady);
