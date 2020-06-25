import Button from "../components/Button";
import DashboardNavigation from "../components/DashboardNavigation";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import routeWithParams from "../utils/routeWithParams";
import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";

/**
 * "Dashboard" - Where a user is redirected to after successfully authenticating.
 */
const Index = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const router = useRouter();

  const handleSubmit = async (event) => {
    event.preventDefault();

    const claim = await appLogic.createClaim();

    // TODO appLogic will handle routing after claim creation
    const route = routeWithParams("claims.checklist", {
      claim_id: claim.application_id,
    });

    router.push(route);
  };

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={router.route} />
      <Title>{t("pages.index.title")}</Title>

      <Heading level="2">{t("pages.index.needForApplyingHeading")}</Heading>
      <ul className="usa-list">
        {t("pages.index.needForApplyingList", { returnObjects: true }).map(
          (listItem, index) => (
            <li key={index}>{listItem}</li>
          )
        )}
      </ul>
      <p>
        <strong>{t("pages.index.applicationTimeEstimate")}</strong>
      </p>

      <form className="margin-bottom-8" onSubmit={handleSubmit}>
        <Button type="submit" name="new-claim">
          {t("pages.index.createClaimButtonText")}
        </Button>
      </form>

      <Heading level="2">{t("pages.index.afterApplyingHeading")}</Heading>
      <p>{t("pages.index.afterApplyingIntro")}</p>
      <ul className="usa-list">
        {t("pages.index.afterApplyingList", { returnObjects: true }).map(
          (listItem, index) => (
            <li key={index}>{listItem}</li>
          )
        )}
      </ul>
      <p>{t("pages.index.afterApplyingOutro")}</p>
    </React.Fragment>
  );
};

Index.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default Index;
