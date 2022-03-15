import Accordion from "../../components/core/Accordion";
import AccordionItem from "../../components/core/AccordionItem";
import Alert from "../../components/core/Alert";
import { AppLogic } from "../../hooks/useAppLogic";
import Button from "../../components/core/Button";
import React from "react";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import User from "../../models/User";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import tracker from "../../services/tracker";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

interface ConsentToDataSharingProps {
  appLogic: AppLogic;
  user: User;
}

export const ConsentToDataSharing = (props: ConsentToDataSharingProps) => {
  const { t } = useTranslation();
  const { appLogic } = props;
  const { updateUser } = appLogic.users;

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    const user = await updateUser(props.user.user_id, {
      consented_to_data_sharing: true,
    });

    // Only navigate away if there are no errors. The user is only returned if there are no errors.
    if (user !== undefined) {
      tracker.trackEvent("User consented to data sharing", {});
      if (isFeatureEnabled("claimantShowMFA") && !user.hasEmployerRole) {
        appLogic.portalFlow.goToPageFor("ENABLE_MFA");
      } else {
        appLogic.portalFlow.goToNextPage({});
      }
    }
  });

  const roleContext = props.user.hasEmployerRole ? "employer" : "user";

  return (
    <form onSubmit={handleSubmit} className="usa-form" method="post">
      <Title>{t("pages.userConsentToDataSharing.title")}</Title>
      <p className="margin-bottom-2">
        {t("pages.userConsentToDataSharing.intro")}
      </p>

      <Accordion>
        <AccordionItem
          heading={t("pages.userConsentToDataSharing.applicationUsageHeading", {
            context: roleContext,
          })}
        >
          <p>{t("pages.userConsentToDataSharing.applicationUsageIntro")}</p>
          <Trans
            i18nKey="pages.userConsentToDataSharing.applicationUsageList"
            tOptions={{ context: roleContext }}
            components={{
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </AccordionItem>

        <AccordionItem
          heading={t("pages.userConsentToDataSharing.dataUsageHeading")}
        >
          <p>
            {t("pages.userConsentToDataSharing.dataUsageBody", {
              context: roleContext,
            })}
          </p>
        </AccordionItem>

        <AccordionItem
          heading={t("pages.userConsentToDataSharing.fullUserAgreementHeading")}
        >
          <p>
            <Trans
              i18nKey="pages.userConsentToDataSharing.fullUserAgreementBody"
              components={{
                // Anchor tag content will be added by Trans component from locale file
                // eslint-disable-next-line jsx-a11y/anchor-has-content
                "informed-consent-link": (
                  <a
                    href={routes.external.massgov.informedConsent}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                // Anchor tag content will be added by Trans component from locale file
                // eslint-disable-next-line jsx-a11y/anchor-has-content
                "privacy-policy-link": (
                  <a
                    href={routes.external.massgov.privacyPolicy}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
              }}
            />
          </p>
        </AccordionItem>
      </Accordion>

      <Alert state="info" noIcon>
        <p>{t("pages.userConsentToDataSharing.agreementBody")}</p>
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.userConsentToDataSharing.continueButton")}
        </Button>
      </Alert>
    </form>
  );
};

export default withUser(ConsentToDataSharing);
