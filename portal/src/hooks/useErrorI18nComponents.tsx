/* eslint sort-keys: ["error", "asc"] */
import React from "react";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Links we support in error messages. Add to this if you need to support new links.
 * Then, in the i18n value, you can reference these using component syntax.
 * @example "Click <some-link>here</some-link> to learn more."
 */
const links: { [i18nComponentName: string]: JSX.Element } = {
  "add-org-link": <a href={routes.employers.addOrganization} />,
  "applying-self-or-unemployed": (
    <a
      target="_blank"
      rel="noreferrer noopener"
      href={routes.external.massgov.applyingSelfOrUnemployed}
    />
  ),
  "applying-to-military-leave": (
    <a
      target="_blank"
      rel="noreferrer noopener"
      href={routes.external.massgov.applyingToMilitaryLeave}
    />
  ),
  "file-a-return-link": (
    <a
      target="_blank"
      rel="noreferrer noopener"
      href={routes.external.massgov.zeroBalanceEmployer}
    />
  ),
  "intermittent-leave-guide": (
    <a
      target="_blank"
      rel="noreferrer noopener"
      href={routes.external.massgov.intermittentLeaveGuide}
    />
  ),
  "mail-fax-instructions": (
    <a
      target="_blank"
      rel="noopener"
      href={routes.external.massgov.mailFaxInstructions}
    />
  ),
  "mass-gov-form-link": (
    <a
      target="_blank"
      rel="noreferrer noopener"
      href={routes.external.massgov.caseCreationErrorGuide}
    />
  ),
  "scheduling-leave-guide": (
    <a
      target="_blank"
      rel="noreferrer noopener"
      href={routes.external.massgov.schedulingLeaveGuide}
    />
  ),
};

/**
 * TODO (PORTAL-372) - Ideally all translated strings had a safelist of allowed components, rather
 * than doing it like this.
 */
const useErrorI18nComponents = () => {
  const { t } = useTranslation();

  const i18nComponents: { [component: string]: JSX.Element } = {
    ...links,
    "contact-center-phone-link": (
      <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
    ),
    /* eslint-disable jsx-a11y/heading-has-content */
    h3: <h3 />,
    li: <li />,
    ul: <ul className="usa-list" />,
  };

  return i18nComponents;
};

export default useErrorI18nComponents;
