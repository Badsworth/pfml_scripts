import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import Heading from "../../../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import formatDateRange from "../../../utils/formatDateRange";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

// TODO (EMPLOYER-363): Update respond by date
const employerDueDate = formatDateRange("2020-10-10");

export const Verification = (props) => {
  const { t } = useTranslation();
  const {
    appLogic,
    query: { absence_id },
  } = props;

  const handleSubmit = (event) => {
    event.preventDefault();
    appLogic.portalFlow.goToNextPage({}, { absence_id });
  };

  return (
    <form onSubmit={handleSubmit} className="usa-form">
      <BackButton />
      <Title>{t("pages.employersClaimsVerification.title")}</Title>
      <Alert state="warning">
        <Trans
          i18nKey="pages.employersClaimsVerification.instructionsDueDate"
          values={{ date: employerDueDate }}
        />
      </Alert>
      <Heading level="2">
        {t("pages.employersClaimsVerification.truthAttestationHeading")}
      </Heading>
      <p>{t("pages.employersClaimsVerification.instructions")}</p>
      <Alert noIcon state="info">
        {t("pages.employersClaimsVerification.agreementBody")}
      </Alert>
      <Button type="submit">
        {t("pages.employersClaimsVerification.submitButton")}
      </Button>
    </form>
  );
};

Verification.propTypes = {
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withUser(Verification);
