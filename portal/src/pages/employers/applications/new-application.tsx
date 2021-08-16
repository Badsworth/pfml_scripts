import React, { useState } from "react";
import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import ConditionalContent from "../../../components/ConditionalContent";
import EmployerClaim from "../../../models/EmployerClaim";
import Heading from "../../../components/Heading";
import InputChoiceGroup from "../../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../../../components/ReviewHeading";
import StatusRow from "../../../components/StatusRow";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import formatDateRange from "../../../utils/formatDateRange";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

export const NewApplication = (props) => {
  const { t } = useTranslation();
  const {
    appLogic: {
      employers: { claim },
      portalFlow,
    },
    query: { absence_id: absenceId },
  } = props;

  // explicitly check for false as opposed to falsy values.
  // temporarily allows the redirect behavior to work even
  // if the API has not been updated to populate the field.
  if (claim.is_reviewable === false) {
    portalFlow.goToPageFor(
      "CLAIM_NOT_REVIEWABLE",
      {},
      { absence_id: absenceId },
      { redirect: true }
    );
  }

  const handleSubmit = (event) => {
    event.preventDefault();

    if (formState.hasReviewerVerified === "true") {
      portalFlow.goToNextPage({}, { absence_id: absenceId });
    } else if (formState.hasReviewerVerified === "false") {
      portalFlow.goToPageFor("CONFIRMATION", {}, { absence_id: absenceId });
    }
  };

  const handleOnChange = (event) => {
    updateFields({
      hasReviewerVerified: event.target.value,
    });
  };

  const [formState, setFormState] = useState({
    hasReviewerVerified: "",
  });

  const updateFields = (fields) => {
    setFormState({ ...formState, ...fields });
  };

  return (
    <React.Fragment>
      <BackButton />
      <Title>
        {t("pages.employersClaimsNewApplication.title", {
          name: claim.fullName,
        })}
      </Title>
      <Alert state="warning">
        <Trans
          i18nKey="pages.employersClaimsNewApplication.instructionsFollowUpDate"
          values={{ date: formatDateRange(claim.follow_up_date) }}
        />
      </Alert>
      <form
        id="employer-verification-form"
        onSubmit={handleSubmit}
        className="usa-form"
        method="post"
      >
        <div className="margin-bottom-2 padding-bottom-2">
          <InputChoiceGroup
            choices={[
              {
                checked: formState.hasReviewerVerified === "true",
                label: t("pages.employersClaimsNewApplication.choiceYes"),
                value: "true",
              },
              {
                checked: formState.hasReviewerVerified === "false",
                label: t("pages.employersClaimsNewApplication.choiceNo"),
                value: "false",
              },
            ]}
            label={
              <ReviewHeading level="2">
                {t("pages.employersClaimsNewApplication.instructionsLabel")}
              </ReviewHeading>
            }
            name="hasReviewerVerified"
            onChange={handleOnChange}
            type="radio"
            smallLabel
          />
        </div>
        {!!claim.employer_dba && (
          <StatusRow
            label={t(
              "pages.employersClaimsNewApplication.organizationNameLabel"
            )}
          >
            {claim.employer_dba}
          </StatusRow>
        )}
        <StatusRow
          label={t("pages.employersClaimsNewApplication.employerIdNumberLabel")}
        >
          {claim.employer_fein}
        </StatusRow>
        <StatusRow
          label={t("pages.employersClaimsNewApplication.employeeNameLabel")}
        >
          {claim.fullName}
        </StatusRow>
        <StatusRow
          label={t("pages.employersClaimsNewApplication.ssnOrItinLabel")}
        >
          {claim.tax_identifier}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsNewApplication.dobLabel")}>
          {formatDateRange(claim.date_of_birth)}
        </StatusRow>
        <ConditionalContent
          updateFields={updateFields}
          visible={
            formState.hasReviewerVerified === "true" ||
            formState.hasReviewerVerified === "false"
          }
        >
          {formState.hasReviewerVerified === "true" && (
            <React.Fragment>
              <Heading level="2">
                {t(
                  "pages.employersClaimsNewApplication.truthAttestationHeading"
                )}
              </Heading>
              <Trans i18nKey="pages.employersClaimsNewApplication.instructions" />
              <Alert noIcon state="info">
                {t("pages.employersClaimsNewApplication.agreementBody")}
              </Alert>
            </React.Fragment>
          )}
          <Button type="submit">
            {t("pages.employersClaimsNewApplication.submitButton", {
              context:
                formState.hasReviewerVerified === "true" ? "secondary" : null,
            })}
          </Button>
        </ConditionalContent>
      </form>
    </React.Fragment>
  );
};

NewApplication.propTypes = {
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      claim: PropTypes.instanceOf(EmployerClaim),
    }).isRequired,
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
      goToNextPage: PropTypes.func.isRequired,
      goToPageFor: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withEmployerClaim(NewApplication);
