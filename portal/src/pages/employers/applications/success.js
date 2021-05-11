import BackButton from "../../../components/BackButton";
import { NewsBanner } from "../../../components/employers/NewsBanner";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

export const Success = (props) => {
  const { t } = useTranslation();
  const {
    appLogic,
    query: { absence_id },
  } = props;
  const showNewsBanner = isFeatureEnabled("employerShowNewsBanner");
  const showDashboard = isFeatureEnabled("employerShowDashboard");

  return (
    <React.Fragment>
      {showDashboard && (
        <BackButton
          label={t("pages.employersClaimsSuccess.backToDashboardLabel")}
          href={appLogic.portalFlow.getNextPageRoute("BACK")}
        />
      )}
      <Title>{t("pages.employersClaimsSuccess.title")}</Title>
      {showNewsBanner && <NewsBanner className="margin-bottom-2" />}
      <Trans
        i18nKey="pages.employersClaimsSuccess.applicationIdLabel"
        values={{ absenceId: absence_id }}
      />
      <p>
        {t("pages.employersClaimsSuccess.instructions_processingApplication")}
      </p>
      <p>
        <Trans
          i18nKey="pages.employersClaimsSuccess.instructions_reimbursement"
          components={{
            "reimbursements-link": (
              <a
                href={routes.external.massgov.employerReimbursements}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
      <UserFeedback url={routes.external.massgov.feedbackEmployer} />
    </React.Fragment>
  );
};

Success.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
    }).isRequired,
  }),
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withUser(Success);
