import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import BenefitsApplication from "../../models/BenefitsApplication";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const CaringLeaveAttestation = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;
  const handleSubmit = () => {
    appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form" method="post">
        <Title>{t("pages.claimsCaringLeaveAttestation.title")}</Title>
        <Alert className="measure-6" state="info" noIcon>
          <Button type="submit">
            {t("pages.claimsCaringLeaveAttestation.submitApplicationButton")}
          </Button>
        </Alert>
      </form>
    </React.Fragment>
  );
};

CaringLeaveAttestation.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withClaim(CaringLeaveAttestation);
