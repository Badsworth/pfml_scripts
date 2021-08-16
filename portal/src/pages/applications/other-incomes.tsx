import BenefitsApplication from "../../models/BenefitsApplication";
import Details from "../../components/Details";
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

export const fields = ["claim.has_other_incomes"];

export const OtherIncomes = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () => {
    if (formState.has_other_incomes === false && claim.other_incomes.length) {
      formState.other_incomes = null;
    }
    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  const hintList = t("pages.claimsOtherIncomes.hintList", {
    returnObjects: true,
  });

  return (
    <QuestionPage
      title={t("pages.claimsOtherIncomes.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_other_incomes")}
        choices={[
          {
            checked: formState.has_other_incomes === true,
            label: t("pages.claimsOtherIncomes.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_other_incomes === false,
            label: t("pages.claimsOtherIncomes.choiceNo"),
            value: "false",
            hint: t("pages.claimsOtherIncomes.choiceNoHint"),
          },
        ]}
        label={t("pages.claimsOtherIncomes.sectionLabel")}
        type="radio"
        hint={
          <React.Fragment>
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
            />
            <p>{t("pages.claimsOtherIncomes.hintHeader")}</p>
            <ul className="usa-list">
              {/* @ts-expect-error ts-migrate(2339) FIXME: Property 'map' does not exist on type 'string'. */}
              {hintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
            <Details
              label={t(
                "pages.claimsOtherIncomes.hintAppliedButNotApprovedDetailsLabel"
              )}
            >
              <Trans
                i18nKey="pages.claimsOtherIncomes.hintAppliedButNotApprovedDetailsBody"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
            </Details>
          </React.Fragment>
        }
      />
    </QuestionPage>
  );
};

OtherIncomes.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(OtherIncomes);
