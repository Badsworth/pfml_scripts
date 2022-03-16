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
    ul: <ul className="usa-list" />,
    li: <li />,
    /* eslint-disable jsx-a11y/heading-has-content */
    h3: <h3 />,
  };

  return i18nComponents;
};

export default useErrorI18nComponents;
