import React, { useEffect } from "react";
import ApplicationCard from "../components/ApplicationCard";
import DashboardNavigation from "../components/DashboardNavigation";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import Title from "../components/Title";
import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";

/**
 * List of all applications associated with the authenticated user
 */
const Applications = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const router = useRouter();

  useEffect(() => {
    appLogic.loadClaims();
  }, [appLogic]);

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={router.route} />
      <Title marginBottom="4">{t("pages.applications.title")}</Title>

      {appLogic.claims ? (
        appLogic.claims.items.map((claim, index) => (
          <ApplicationCard
            key={claim.application_id}
            claim={claim}
            number={index + 1}
          />
        ))
      ) : (
        <Spinner aria-valuetext={t("components.spinner.label")} />
      )}
    </React.Fragment>
  );
};

Applications.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default Applications;
