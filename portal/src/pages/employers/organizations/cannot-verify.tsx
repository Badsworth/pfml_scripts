import { Trans, useTranslation } from "react-i18next";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import BackButton from "../../../components/BackButton";
import Lead from "../../../components/core/Lead";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import routes from "../../../routes";

export const CannotVerify = (
  props: WithUserProps & { query: { employer_id?: string } }
) => {
  const { query, user } = props;
  const employer = user.user_leave_administrators.find((employer) => {
    return employer.employer_id === query.employer_id;
  });
  const { t } = useTranslation();

  if (!employer) {
    return <PageNotFound />;
  }

  const employerDba = employer.employer_dba;
  const employerFein = employer.employer_fein;

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.employersCannotVerify.title")}</Title>
      <Lead>
        <Trans
          i18nKey="pages.employersCannotVerify.companyNameLabel"
          tOptions={{ employerDba }}
        />
        <br />
        <Trans
          i18nKey="pages.employersCannotVerify.employerIdNumberLabel"
          tOptions={{ employerFein }}
        />
      </Lead>
      <p>
        <Trans
          i18nKey="pages.employersCannotVerify.body"
          components={{
            "learn-more-link": (
              <a
                href={routes.external.massgov.verifyEmployer}
                target="_blank"
                rel="noopener"
              />
            ),
            "dor-phone-link": (
              <a href={`tel:${t("shared.departmentOfRevenuePhoneNumber")}`} />
            ),
          }}
        />
      </p>
    </React.Fragment>
  );
};

export default withUser(CannotVerify);
