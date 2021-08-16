import BenefitsApplication, {
  RelationshipToCaregiver,
} from "../../models/BenefitsApplication";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
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

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.claimsCaringLeaveAttestation.title")}</Title>
      <Trans
        i18nKey="pages.claimsCaringLeaveAttestation.lead"
        components={{
          "caregiver-relationship-link": (
            <a
              target="_blank"
              rel="noopener"
              href={routes.external.massgov.caregiverRelationship}
            />
          ),
        }}
      />
      <Alert className="measure-6" state="info" noIcon>
        <p>
          {t("pages.claimsCaringLeaveAttestation.truthAttestation", {
            context: findKeyByValue(RelationshipToCaregiver, relationship),
          })}
        </p>
        <ButtonLink
          className="text-no-underline text-white"
          href={appLogic.portalFlow.getNextPageRoute("CONTINUE", {}, query)}
        >
          {t("pages.claimsCaringLeaveAttestation.submitApplicationButton")}
        </ButtonLink>
      </Alert>
    </React.Fragment>
  );
};

CaringLeaveAttestation.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
    }),
  }).isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(CaringLeaveAttestation);
