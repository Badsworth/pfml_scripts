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

const Checklist = (props) => {
  // TODO: add appErrors.warnings when API validations are in place
  // https://lwd.atlassian.net/browse/CP-509
  const steps = StepModel.createClaimStepsFromMachine(
    machineConfigs,
    { claim: props.claim, user: props.appLogic.users.user },
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
        submitButtonText={t("pages.claimsChecklist.submitButton")}
        submitPage={routeWithParams("claims.review", {
          claim_id: props.claim.application_id,
        })}
        submitPageDisabled={!allStepsComplete}
        startText={t("pages.claimsChecklist.start")}
        resumeText={t("pages.claimsChecklist.resume")}
        completedText={t("pages.claimsChecklist.completed")}
        editText={t("pages.claimsChecklist.edit")}
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
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(Claim).isRequired,
};

export default withClaim(Checklist);
