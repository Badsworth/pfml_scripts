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
      <Title>{t("pages.index.title")}</Title>

      <Heading level="2">{t("pages.index.needForApplyingHeading")}</Heading>
      <ul className="usa-list">
        <li>{t("pages.index.needForApplyingList.proofOfIdentity")}</li>
        <li>{t("pages.index.needForApplyingList.ssnItin")}</li>
        <li>{t("pages.index.needForApplyingList.leaveReason")}</li>
        <li>
          <Trans
            i18nKey="pages.index.needForApplyingList.healthcareProviderForm"
            components={{
              "healthcare-provider-form-link": (
                <a href={routes.external.massgov.healthcareProviderForm} />
              ),
            }}
          />
        </li>
        <li>{t("pages.index.needForApplyingList.employerFein")}</li>
        <li>{t("pages.index.needForApplyingList.leaveDates")}</li>
        <li>{t("pages.index.needForApplyingList.paymentInformation")}</li>
      </ul>
      <p>
        <strong>{t("pages.index.applicationTimeEstimate")}</strong>
      </p>

      <form className="margin-bottom-8" onSubmit={handleSubmit}>
        <Button type="submit" name="new-claim">
          {t("pages.index.createClaimButton")}
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

export default withUser(Index);
