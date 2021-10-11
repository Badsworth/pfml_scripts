import { Trans, useTranslation } from "react-i18next";
import BackButton from "../../../components/BackButton";
import Lead from "../../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import User from "../../../models/User";
import routes from "../../../routes";
import withUser from "../../../hoc/withUser";

export const CannotVerify = (props) => {
  const { appLogic, query } = props;
  const {
    users: { user },
  } = appLogic;
  const employer = user.user_leave_administrators.find((employer) => {
    return employer.employer_id === query.employer_id;
  });
  const { t } = useTranslation();
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

CannotVerify.propTypes = {
  appLogic: PropTypes.shape({
    users: PropTypes.shape({
      user: PropTypes.instanceOf(User).isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    employer_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withUser(CannotVerify);
