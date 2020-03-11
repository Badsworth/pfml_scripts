import Heading from "./Heading";
import Lead from "./Lead";
import PropType from "prop-types";
import React from "react";
import Title from "./Title";
import WagesTable from "./WagesTable";
import { useTranslation } from "react-i18next";

/**
 * A view that is conditionally rendered on the Result page when the claimant is ineligible due to insufficient contributions.
 */
const Ineligible = props => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Title>{t("components.ineligible.title")}</Title>
      <WagesTable employeeId={props.employeeId} eligibility="ineligible" />

      <Heading level="2">{t("components.ineligible.optionsHeading")}</Heading>

      <Heading level="3">{t("components.ineligible.option1Heading")}</Heading>
      <Lead>{t("components.ineligible.option1Description")}</Lead>

      <Heading level="3">{t("components.ineligible.option2Heading")}</Heading>
      <Lead>{t("components.ineligible.option2Description")}</Lead>
    </React.Fragment>
  );
};

Ineligible.propTypes = {
  /**
   * Id for employee whose result will be displayed
   */
  employeeId: PropType.string.isRequired,
};

export default Ineligible;
