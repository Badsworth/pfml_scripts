import BackButton from "../../components/BackButton";
import Claim from "../../models/Claim";
import PropTypes from "prop-types";
import React from "react";
import Step from "../../components/Step";
import StepList from "../../components/StepList";
import StepModel from "../../models/Step";
import machineConfigs from "../../routes/claim-flow-configs";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const Checklist = (props) => {
  // TODO: add appErrors.warnings when API validations are in place
  // https://lwd.atlassian.net/browse/CP-509
  const steps = StepModel.createClaimStepsFromMachine(
    machineConfigs,
    props.claim,
    null
  );

  const allStepsComplete = steps.every((step) => step.isComplete);
  const { t } = useTranslation();

  return (
    <div className="measure-6">
      <BackButton
        label={t("pages.claimsChecklist.backButtonLabel")}
        href={routes.claims.dashboard}
      />
      <StepList
        title={t("pages.claimsChecklist.stepListTitle")}
        submitButtonText={t("pages.claimsChecklist.submitButtonText")}
        submitPage={routeWithParams("claims.review", {
          claim_id: props.claim.application_id,
        })}
        submitPageDisabled={!allStepsComplete}
        startText={t("pages.claimsChecklist.startText")}
        resumeText={t("pages.claimsChecklist.resumeText")}
        completedText={t("pages.claimsChecklist.completedText")}
        editText={t("pages.claimsChecklist.editText")}
        screenReaderNumberPrefix={t(
          "pages.claimsChecklist.screenReaderNumberPrefix"
        )}
      >
        {steps.map((step) => (
          <Step
            key={step.name}
            title={t("pages.claimsChecklist.stepTitle", { context: step.name })}
            status={step.status}
            stepHref={step.href}
          >
            <span
              dangerouslySetInnerHTML={{
                __html: t("pages.claimsChecklist.stepHTMLDescription", {
                  context: step.name,
                }),
              }}
            />
          </Step>
        ))}
      </StepList>
    </div>
  );
};

Checklist.propTypes = {
  claim: PropTypes.instanceOf(Claim),
};

export default withClaim(Checklist);
