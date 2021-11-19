import withUser, { WithUserProps } from "../../../hoc/withUser";
import Button from "../../../components/core/Button";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Success = (
  props: WithUserProps & { query: { employer_id?: string; next?: string } }
) => {
  const { appLogic, query, user } = props;
  const { t } = useTranslation();

  const employer = user.user_leave_administrators.find((employer) => {
    return employer.employer_id === query.employer_id;
  });
  const navigateToNextPage = () => {
    const route = query.next || routes.employers.organizations;
    appLogic.portalFlow.goTo(route);
  };

  if (!employer) {
    return <PageNotFound />;
  }

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

export default withUser(Success);
