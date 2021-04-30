import BenefitsApplication, {
  RelationshipToCaregiver,
} from "../../models/BenefitsApplication";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import { get } from "lodash";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const CaringLeaveAttestation = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;
  const relationship = get(
    claim,
    "leave_details.caring_leave_metadata.relationship_to_caregiver"
  );

  const handleSubmit = () => {
    appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form" method="post">
        <Title>{t("pages.claimsCaringLeaveAttestation.title")}</Title>
        <Trans
          i18nKey="pages.claimsCaringLeaveAttestation.lead"
          components={{
            "eligible-relationship-link": (
              <a href={routes.external.caregiverRelationship} />
            ),
          }}
        />
        <Alert className="measure-6" state="info" noIcon>
          <p>
            {t("pages.claimsCaringLeaveAttestation.truthAttestation", {
              context: findKeyByValue(RelationshipToCaregiver, relationship),
            })}
          </p>
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

export default withBenefitsApplication(CaringLeaveAttestation);
