import * as React from "react";
import BackButton from "../../components/BackButton";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

export const Status = (props) => {
  const { t } = useTranslation();
  const { appLogic } = props;
  const { portalFlow } = appLogic;

  React.useEffect(() => {
    if (!isFeatureEnabled("claimantShowStatusPage")) {
      portalFlow.goTo(routes.applications.index);
    }
  }, [portalFlow]);

  const containerClassName = "border-top border-base-lighter padding-top-2";

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <Title weight="normal" small={true}>
          {t("pages.claimsStatus.applicationDetails")}
        </Title>

        {/* Heading section */}

        <Heading level="2" size="1">
          {/* // TODO (CP-2449): placeholder */}
          Leave Reason
        </Heading>
        <div className="display-flex border-base-lighter margin-bottom-3 bg-base-lightest padding-2">
          <div className="padding-right-10">
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.applicationID")}
            </Heading>
            {/* // TODO (CP-2449): placeholder */}
            <p className="text-bold">Fineos-Absence-ID</p>
          </div>
          <div>
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.employerEIN")}
            </Heading>
            {/* // TODO (CP-2449): placeholder */}
            <p className="text-bold">123456789</p>
          </div>
        </div>

        {/* Manage applications section */}
        <div className={containerClassName}>
          <Heading level="2">
            {t("pages.claimsStatus.manageApplicationHeading")}
          </Heading>
          <Heading level="3">
            {t("pages.claimsStatus.makeChangesHeading")}
          </Heading>
          <Trans
            i18nKey="pages.claimsStatus.makeChangesBody"
            components={{
              "contact-center-phone-link": (
                <a
                  href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`}
                />
              ),
            }}
          />
          <Heading level="3">
            {t("pages.claimsStatus.reportOtherBenefitsHeading")}
          </Heading>
          <Trans
            i18nKey="pages.claimsStatus.reportOtherBenefitsBody"
            components={{
              "contact-center-phone-link": (
                <a
                  href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`}
                />
              ),
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </div>
      </div>
    </React.Fragment>
  );
};

Status.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default Status;
