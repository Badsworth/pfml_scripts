import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import BackButton from "src/components/BackButton";
import ButtonLink from "src/components/ButtonLink";
import Heading from "src/components/core/Heading";
import React from "react";
import Title from "src/components/core/Title";
import { useTranslation } from "../../locales/i18n";

export const fields = [];

/**
 * A form page to begin collecting additional information for an employee/employer match.
 */
export const AdditionalUserNotFoundInfoBegin = (
  props: WithBenefitsApplicationProps
) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <BackButton />
      <Title small={true}>{t("pages.claimsEmploymentStatus.title")}</Title>
      <Heading level="2" size="1">
        {t(
          "pages.claimsAdditionalUserNotFoundInfo.beginAdditionalNoEmployeeFoundInfoTitle"
        )}
      </Heading>
      <p className="display-block line-height-sans-5 measure-5 usa-intro">
        {t(
          "pages.claimsAdditionalUserNotFoundInfo.beginAdditionalNoEmployeeFoundInfoDescription"
        )}
      </p>
      <ButtonLink
        className="display-inline-flex flex-align-center flex-justify-center flex-column margin-right-0 margin-top-3"
        href={appLogic.portalFlow.getNextPageRoute(
          "CONTINUE",
          {},
          { claim_id: claim.application_id }
        )}
      >
        <div>
          {t(
            "pages.claimsAdditionalUserNotFoundInfo.beginAdditionalNoEmployeeFoundInfoButton"
          )}
        </div>
      </ButtonLink>
    </React.Fragment>
  );
};

export default withBenefitsApplication(AdditionalUserNotFoundInfoBegin);
