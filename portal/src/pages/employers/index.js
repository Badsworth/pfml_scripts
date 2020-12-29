import { IconMail, IconPdf } from "@massds/mayflower-react/dist/Icon";
import Heading from "../../components/Heading";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

// TODO (EMPLOYER-555) import from @massds when available
const IconWait = (props) => (
  <svg aria-hidden="true" viewBox="0 0 40 40" {...props}>
    <path d="M40 20c0 11.045-8.96 20-20.01 20-1.8 0-3.54-.26-5.2-.705l1.11-3.157c1.31.332 2.68.529 4.09.529 9.2 0 16.68-7.477 16.68-16.667 0-9.19-7.48-16.667-16.68-16.667-3.72 0-7.15 1.24-9.93 3.316l3.42 3.414L1.79 12.32 4.05.632 7.68 4.27C11.08 1.607 15.34 0 19.99 0 31.04 0 40 8.955 40 20zM21.67 10v10H30v3.333H18.33V10zM5.78 28.667c.56.91 1.2 1.761 1.91 2.546l-2.34 2.389a20.092 20.092 0 01-2.56-3.43zm2.04 7.181l2.36-2.405a16.69 16.69 0 002.59 1.555l-1.11 3.165a19.847 19.847 0 01-3.84-2.315zM4.33 25.662l-2.99 1.51a19.43 19.43 0 01-1.09-4.101l3.33-.264c.16.983.42 1.936.75 2.855zM0 19.748l3.36-.268c.04-1.172.21-2.31.48-3.412H.38c-.24 1.19-.36 2.422-.38 3.68z" />
  </svg>
);

const showMedicalLeave = isFeatureEnabled("claimantShowMedicalLeaveType");

export const Index = () => {
  const { t } = useTranslation();
  const iconProps = {
    className: "margin-right-2 text-secondary text-middle",
    height: 30,
    width: 30,
    fill: "currentColor",
  };

  return (
    <div className="grid-container">
      <div className="grid-row">
        <div className="desktop:grid-col-8">
          <Title>{t("pages.employersDashboard.welcomeTitle")}</Title>
          <p>
            {t("pages.employersDashboard.welcomeBody", {
              context: showMedicalLeave ? null : "prelaunch",
            })}
          </p>

          <Heading level="2">
            <IconMail {...iconProps} />
            {t("pages.employersDashboard.checkEmailTitle")}
          </Heading>
          <p>{t("pages.employersDashboard.checkEmailBody")}</p>

          <Heading level="2">
            <IconWait {...iconProps} />
            {t("pages.employersDashboard.respondTitle")}
          </Heading>
          <p>{t("pages.employersDashboard.respondBody")}</p>

          <Heading level="2">
            <IconPdf {...iconProps} />
            {t("pages.employersDashboard.viewFormsTitle")}
          </Heading>
          <p>
            <Trans
              i18nKey="pages.employersDashboard.viewFormsBody"
              components={{
                "healthcare-provider-form-link": (
                  <a
                    href={routes.external.massgov.healthcareProviderForm}
                    target="_blank"
                    rel="noopener"
                  />
                ),
              }}
            />
          </p>
        </div>
        <div className="grid-col-fill" />
        <aside className="desktop:grid-col-3 margin-top-7 desktop:margin-top-1">
          <Heading level="2">
            {t("pages.employersDashboard.learnMoreTitle")}
          </Heading>
          <Trans
            i18nKey="pages.employersDashboard.learnMoreLinks"
            components={{
              ul: (
                <ul className="usa-list desktop:font-body-2xs desktop:padding-top-05" />
              ),
              li: <li />,
              // TODO (EMPLOYER-555) Add links
              "mass-employer-role-link": (
                <a
                  href={routes.external.massgov.employersGuide}
                  target="_blank"
                  rel="noopener"
                />
              ),
              "reimbursements-link": (
                <a
                  href={routes.external.massgov.employerReimbursements}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
          />
        </aside>
      </div>
    </div>
  );
};

export default withUser(Index);
