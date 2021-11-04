import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import React from "react";
import { RelationshipToCaregiver } from "../../models/BenefitsApplication";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import { get } from "lodash";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

export const CaringLeaveAttestation = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
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
          href={appLogic.portalFlow.getNextPageRoute(
            "CONTINUE",
            {},
            { claim_id: claim.application_id }
          )}
        >
          {t("pages.claimsCaringLeaveAttestation.submitApplicationButton")}
        </ButtonLink>
      </Alert>
    </React.Fragment>
  );
};

export default withBenefitsApplication(CaringLeaveAttestation);
