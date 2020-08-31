import Accordion from "../components/Accordion";
import AccordionItem from "../components/AccordionItem";
import Button from "../components/Button";
import DashboardNavigation from "../components/DashboardNavigation";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";
import withUser from "../hoc/withUser";

/**
 * "Dashboard" - Where a user is redirected to after successfully authenticating.
 */
const Index = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const router = useRouter();

  const handleSubmit = async (event) => {
    event.preventDefault();
    await appLogic.claims.create();
  };

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={router.route} />
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

        <form className="margin-bottom-8" onSubmit={handleSubmit}>
          <Button type="submit" name="new-claim">
            {t("pages.index.createClaimButton")}
          </Button>
        </form>
      </div>
    </React.Fragment>
  );
};

Index.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Index);
