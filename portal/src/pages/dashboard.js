import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import Accordion from "../components/Accordion";
import AccordionItem from "../components/AccordionItem";
import ButtonLink from "../components/ButtonLink";
import DashboardNavigation from "../components/DashboardNavigation";
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
  const iconProps = {
    className: "margin-right-2 text-secondary text-middle",
    height: 30,
    width: 30,
    fill: "currentColor",
  };

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={appLogic.portalFlow.pathname} />
      <div className="measure-6">
        <Title>{t("pages.dashboard.title")}</Title>

        <Heading level="2">
          <IconLaptop {...iconProps} />
          {t("pages.dashboard.applyOnlineTitle")}
        </Heading>

        <Trans
          i18nKey="pages.dashboard.applyOnline"
          components={{
            p: <p />,
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <Heading level="2">
          <IconPhone {...iconProps} />
          {t("pages.dashboard.applyByPhoneTitle")}
        </Heading>

        <Trans
          i18nKey="pages.dashboard.applyByPhone"
          components={{
            p: <p />,
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <Trans
          i18nKey="pages.dashboard.applyMore"
          components={{
            p: <p />,
            a: <a />,
          }}
        />

        <hr className="margin-top-4" />

        <Heading level="2" size="1" className="margin-top-4">
          {t("pages.dashboard.stepsTitle")}
        </Heading>

        <Heading level="3" size="2">
          {t("pages.dashboard.stepOneHeading")}
        </Heading>

        <p>{t("pages.dashboard.stepOneLeadLine1")}</p>
        <p>{t("pages.dashboard.stepOneLeadLine2")}</p>

        <Heading level="3" size="2">
          {t("pages.dashboard.stepTwoHeading")}
        </Heading>

        <div className="measure-4">
          <Accordion>
            <AccordionItem heading={t("pages.dashboard.medicalLeaveHeading")}>
              <p>
                <Trans
                  i18nKey="pages.dashboard.medicalLeaveBody"
                  components={{
                    "healthcare-provider-form-link": (
                      <a
                        href={routes.external.massgov.healthcareProviderForm}
                      />
                    ),
                  }}
                />
              </p>
            </AccordionItem>
            <AccordionItem
              heading={t("pages.dashboard.familyLeaveAfterBirthHeading")}
            >
              <p>{t("pages.dashboard.familyLeaveAfterBirthBodyLine1")}</p>
              <p>{t("pages.dashboard.familyLeaveAfterBirthBodyLine2")}</p>
            </AccordionItem>
            <AccordionItem
              heading={t("pages.dashboard.familyLeaveAfterAdoptionHeading")}
            >
              <p>{t("pages.dashboard.familyLeaveAfterAdoptionBody")}</p>
            </AccordionItem>
          </Accordion>
        </div>

        <Heading level="3" size="2">
          {t("pages.dashboard.stepThreeHeading")}
        </Heading>

        <p>{t("pages.dashboard.stepThreeLead")}</p>
        <p>{t("pages.dashboard.multipleApplicationsListIntro")}</p>
        <ul className="usa-list">
          <li>
            <Trans
              i18nKey="pages.dashboard.multipleApplicationsList_pregnancy"
              components={{
                "gestational-parents-overview-link": (
                  <a href={routes.external.massgov.gestationalParentOverview} />
                ),
              }}
            />
          </li>
          <li>
            {t("pages.dashboard.multipleApplicationsList_multipleEmployers")}
          </li>
          <li>{t("pages.dashboard.multipleApplicationsList_intermittent")}</li>
        </ul>

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
