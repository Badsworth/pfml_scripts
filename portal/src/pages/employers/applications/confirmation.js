import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../../components/UserFeedback";
import formatDateRange from "../../../utils/formatDateRange";
import routes from "../../../../src/routes";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

export const Confirmation = (props) => {
  const { t } = useTranslation();
  const { absence_id, follow_up_date } = props.query;

  return (
    <React.Fragment>
      <Title>{t("pages.employersClaimsConfirmation.title")}</Title>
      <Trans
        i18nKey="pages.employersClaimsConfirmation.applicationIdLabel"
        values={{ absenceId: absence_id }}
      />
      {follow_up_date && (
        <Trans
          i18nKey="pages.employersClaimsConfirmation.instructionsFollowUpDateLabel"
          values={{ date: formatDateRange(follow_up_date) }}
          components={{
            div: <div />,
          }}
        />
      )}
      <Trans
        i18nKey="pages.employersClaimsConfirmation.instructions"
        components={{
          p: <p />,
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
      <p>
        <Trans
          i18nKey="pages.employersClaimsConfirmation.instructions_benefitsGuide"
          components={{
            "benefits-guide-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.benefitsGuide}
              />
            ),
          }}
        />
      </p>
      <UserFeedback url={routes.external.massgov.feedbackEmployer} />
    </React.Fragment>
  );
};

Confirmation.propTypes = {
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
    follow_up_date: PropTypes.string,
  }).isRequired,
};

export default withUser(Confirmation);
