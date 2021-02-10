import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import {
  faComments,
  faEdit,
  faFile,
} from "@fortawesome/free-regular-svg-icons";
import Alert from "../components/Alert";
import ButtonLink from "../components/ButtonLink";
import ClaimCollection from "../models/ClaimCollection";
import DashboardNavigation from "../components/DashboardNavigation";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";
import withClaims from "../hoc/withClaims";

/**
 * "Dashboard" - Where a Claimant is redirected to after successfully authenticating.
 */
export const Dashboard = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  // We only want to redirect users who have claims when they
  // first login, but don't want to prevent them from navigating
  // to this page entirely
  if (props.query["logged-in"] && !props.claims.isEmpty) {
    appLogic.portalFlow.goToPageFor("SHOW_APPLICATIONS");
  }

  const alertIconProps = {
    className: "margin-right-1 text-secondary text-middle",
    height: 20,
    width: 20,
    fill: "currentColor",
  };

  const iconProps = {
    className: "margin-right-1 text-secondary",
    size: "lg",
    fixedWidth: true,
  };

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={appLogic.portalFlow.pathname} />

      <Title>{t("pages.dashboard.title")}</Title>

      <Alert
        heading={t("pages.dashboard.alertHeading")}
        state="info"
        neutral
        className="margin-bottom-3"
      >
        <Heading level="3" className="margin-top-3">
          <IconLaptop {...alertIconProps} />
          {t("pages.dashboard.alertOnlineHeading")}
        </Heading>

        <Trans
          i18nKey="pages.dashboard.alertOnline"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <Heading level="3">
          <IconPhone {...alertIconProps} />
          {t("pages.dashboard.alertPhoneHeading")}
        </Heading>

        <Trans
          i18nKey="pages.dashboard.alertPhone"
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
          <FontAwesomeIcon icon={faComments} {...iconProps} />
          {t("pages.dashboard.stepOneHeading")}
        </Heading>
        <Trans i18nKey="pages.dashboard.stepOne" />

        <Heading level="2">
          <FontAwesomeIcon icon={faFile} {...iconProps} />
          {t("pages.dashboard.stepTwoHeading")}
        </Heading>
        <Trans
          i18nKey="pages.dashboard.stepTwo"
          components={{
            "healthcare-provider-form-link": (
              <a href={routes.external.massgov.healthcareProviderForm} />
            ),
          }}
        />

        <Heading level="2">
          <FontAwesomeIcon icon={faEdit} {...iconProps} />
          {t("pages.dashboard.stepThreeHeading")}
        </Heading>
        <Trans
          i18nKey="pages.dashboard.stepThree"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            "medical-bonding-link": (
              <a href={routes.external.massgov.medicalBonding} />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <ButtonLink
          className="margin-top-3 margin-bottom-8"
          href={appLogic.portalFlow.getNextPageRoute("START_APPLICATION")}
        >
          {t("pages.dashboard.createClaimButton")}
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

Dashboard.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      goToPageFor: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }),
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
  query: PropTypes.shape({
    "logged-in": PropTypes.string,
  }).isRequired,
};

export default withClaims(Dashboard);
