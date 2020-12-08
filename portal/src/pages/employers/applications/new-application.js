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
import { get } from "lodash";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

export const NewApplication = (props) => {
  const { t } = useTranslation();
  const {
    appLogic: {
      employers: { claim },
    },
    query: { absence_id: absenceId },
  } = props;

  const handleSubmit = (event) => {
    event.preventDefault();

    if (formState.hasReviewerVerified === "true") {
      props.appLogic.portalFlow.goToNextPage({}, { absence_id: absenceId });
    } else if (formState.hasReviewerVerified === "false") {
      props.appLogic.portalFlow.goToPageFor(
        "CONFIRMATION",
        {},
        { absence_id: absenceId, follow_up_date: claim.follow_up_date }
      );
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

  const getField = (fieldName) => {
    return get(formState, fieldName);
  };

  const updateFields = (fields) => {
    setFormState({ ...formState, ...fields });
  };

  const clearField = () => {
    setFormState({
      hasReviewerVerified: "",
    });
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
      >
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
        <StatusRow
          label={t("pages.employersClaimsNewApplication.employeeNameLabel")}
          className="margin-top-2 padding-top-2"
        >
          {claim.fullName}
        </StatusRow>
        <StatusRow
          label={t("pages.employersClaimsNewApplication.employerIdNumberLabel")}
        >
          {claim.tax_identifier}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsNewApplication.dobLabel")}>
          {formatDateRange(claim.date_of_birth)}
        </StatusRow>
        <ConditionalContent
          getField={getField}
          clearField={clearField}
          updateFields={updateFields}
          visible={
            formState.hasReviewerVerified === "true" ||
            formState.hasReviewerVerified === "false"
          }
        >
          <Heading level="2">
            {t("pages.employersClaimsNewApplication.truthAttestationHeading")}
          </Heading>
          <Trans i18nKey="pages.employersClaimsNewApplication.instructions" />
          <Alert noIcon state="info">
            {t("pages.employersClaimsNewApplication.agreementBody")}
          </Alert>
          <Button type="submit">
            {t("pages.employersClaimsNewApplication.submitButton")}
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
      goToNextPage: PropTypes.func.isRequired,
      goToPageFor: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withEmployerClaim(NewApplication);
