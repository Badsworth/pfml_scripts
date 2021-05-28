import BenefitsApplication from "../../models/BenefitsApplication";
import Details from "../../components/Details";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.has_concurrent_leave"];

export const ConcurrentLeaves = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSave = () => {
    if (formState.has_concurrent_leave === false && claim.concurrent_leave) {
      formState.concurrent_leave = null;
    }
    appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  return (
    <QuestionPage
      title={t("pages.claimsConcurrentLeaves.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_concurrent_leave")}
        choices={[
          {
            checked: formState.has_concurrent_leave === true,
            label: t("pages.claimsConcurrentLeaves.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_concurrent_leave === false,
            label: t("pages.claimsConcurrentLeaves.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsConcurrentLeaves.sectionLabel")}
        type="radio"
        hint={
          <React.Fragment>
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
            />
            <Heading level="3">
              {t("pages.claimsConcurrentLeaves.hintWhatKindHeading")}
            </Heading>
            <Trans i18nKey="pages.claimsConcurrentLeaves.hintWhatKindBody" />
            <Heading level="3">
              {t("pages.claimsConcurrentLeaves.hintWhenToReportHeading")}
            </Heading>
            <Trans
              i18nKey="pages.claimsConcurrentLeaves.hintWhenToReportBody"
              components={{ ul: <ul className="usa-list" />, li: <li /> }}
            />
            <Details
              label={t(
                "pages.claimsConcurrentLeaves.hintWhenToReportDetailsLabel"
              )}
            >
              <Trans
                i18nKey="pages.claimsConcurrentLeaves.hintWhenToReportDetailsBody"
                components={{ ul: <ul className="usa-list" />, li: <li /> }}
              />
            </Details>
          </React.Fragment>
        }
      />
    </QuestionPage>
  );
};

ConcurrentLeaves.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(ConcurrentLeaves);
