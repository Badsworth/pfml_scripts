import Button from "../../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import User from "../../../models/User";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

export const Success = (props) => {
  const { appLogic, query, user } = props;
  const { t } = useTranslation();

  const employer = user.user_leave_administrators.find((employer) => {
    return employer.employer_id === query.employer_id;
  });
  const navigateToNextPage = () => {
    const route = query.next || routes.employers.organizations;
    appLogic.portalFlow.goTo(route);
  };

  return (
    <React.Fragment>
      <Title>{t("pages.employersOrganizationsSuccess.title")}</Title>
      <p>
        <Trans
          i18nKey="pages.employersOrganizationsSuccess.companyNameLabel"
          tOptions={{ company: employer.employer_dba }}
        />
        <br />
        <Trans
          i18nKey="pages.employersOrganizationsSuccess.employerIdNumberLabel"
          tOptions={{ ein: employer.employer_fein }}
        />
      </p>
      <p>
        <Trans
          i18nKey="pages.employersOrganizationsSuccess.instructions"
          components={{
            "learn-more-link": (
              <a
                href={routes.external.massgov.employerAccount}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
      <Button onClick={navigateToNextPage}>
        {t("pages.employersOrganizationsSuccess.continueButton")}
      </Button>
    </React.Fragment>
  );
};

Success.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    employer_id: PropTypes.string.isRequired,
    next: PropTypes.string.isRequired,
  }).isRequired,
  user: PropTypes.instanceOf(User),
};

export default withUser(Success);
