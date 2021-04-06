import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * A summary box that highlights key information.
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/summary-box/)
 */
function DocumentRequirements(props) {
  const { t } = useTranslation();
  return (
    <div className="usa-summary-box margin-bottom-2" role="complementary">
      <div className="usa-summary-box__body">
        <Heading className="usa-summary-box__heading" level="3" size="4">
          {t("components.documentRequirements.header")}
        </Heading>
        <div className="usa-summary-box__text">
          <Trans
            i18nKey="components.documentRequirements.body"
            tOptions={{ context: props.type }}
            components={{
              ul: <ul className="usa-list" />,
              li: <li />,
              "mail-fax-instructions-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.mailFaxInstructions}
                />
              ),
            }}
          />
        </div>
      </div>
    </div>
  );
}

DocumentRequirements.propTypes = {
  type: PropTypes.oneOf(["id", "certification"]),
};

export default DocumentRequirements;
