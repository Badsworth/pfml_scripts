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
export const Index = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={appLogic.portalFlow.pathname} />
      <div className="measure-6">
        <Title>{t("pages.index.title")}</Title>

        <Heading level="2">{t("pages.index.stepOneHeading")}</Heading>
        <p>{t("pages.index.stepOneLeadLine1")}</p>
        <p>{t("pages.index.stepOneLeadLine2")}</p>
        <Heading level="2">{t("pages.index.stepTwoHeading")}</Heading>
        <div className="measure-4">
          <Accordion>
            <AccordionItem heading={t("pages.index.medicalLeaveHeading")}>
              <p>
                <Trans
                  i18nKey="pages.index.medicalLeaveBody"
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
              heading={t("pages.index.familyLeaveAfterBirthHeading")}
            >
              <p>{t("pages.index.familyLeaveAfterBirthBodyLine1")}</p>
              <p>{t("pages.index.familyLeaveAfterBirthBodyLine2")}</p>
            </AccordionItem>
            <AccordionItem
              heading={t("pages.index.familyLeaveAfterAdoptionHeading")}
            >
              <p>{t("pages.index.familyLeaveAfterAdoptionBody")}</p>
            </AccordionItem>
          </Accordion>
        </div>

        <Heading level="2">{t("pages.index.stepThreeHeading")}</Heading>
        <p>{t("pages.index.stepThreeLead")}</p>
        <p>{t("pages.index.multipleApplicationsListIntro")}</p>
        <ul className="usa-list">
          <li>{t("pages.index.multipleApplicationsList_pregnancy")}</li>
          <li>{t("pages.index.multipleApplicationsList_multipleEmployers")}</li>
          <li>{t("pages.index.multipleApplicationsList_intermittent")}</li>
        </ul>

        <ButtonLink
          className="margin-top-3 margin-bottom-8"
          href={routes.claims.start}
        >
          {t("pages.index.createClaimButton")}
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

Index.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Index);
