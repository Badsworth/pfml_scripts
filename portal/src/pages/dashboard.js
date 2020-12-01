import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import {
  faComments,
  faEdit,
  faFile,
} from "@fortawesome/free-regular-svg-icons";
import Alert from "../components/Alert";
import ButtonLink from "../components/ButtonLink";
import DashboardNavigation from "../components/DashboardNavigation";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";
import withUser from "../hoc/withUser";

/**
 * "Dashboard" - Where a Claimant is redirected to after successfully authenticating.
 */
export const Dashboard = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

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
        <Title>{t("pages.dashboard.title")}</Title>

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
            "medical-bonding-link": (
              <a href={routes.external.massgov.medicalBonding} />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <ButtonLink
          className="margin-top-3 margin-bottom-8"
          href={routes.applications.start}
        >
          {t("pages.dashboard.createClaimButton")}
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

Dashboard.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Dashboard);
