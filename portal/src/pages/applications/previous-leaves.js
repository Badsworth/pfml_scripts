import BenefitsApplication from "../../models/BenefitsApplication";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { pick } from "lodash";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.has_previous_leaves"];

export const PreviousLeaves = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () => {
    if (
      formState.has_previous_leaves === false &&
      claim.previous_leaves.length
    ) {
      formState.previous_leaves = null;
    }
    appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeaves.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_previous_leaves")}
        choices={[
          {
            checked: formState.has_previous_leaves === true,
            label: t("pages.claimsPreviousLeaves.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_previous_leaves === false,
            label: t("pages.claimsPreviousLeaves.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsPreviousLeaves.sectionLabel")}
        type="radio"
        hint={
          <div>
            <Details label={t("pages.claimsPreviousLeaves.detailsLabel")}>
              <p>{t("pages.claimsPreviousLeaves.hintHeader")}</p>
              <ul className="usa-list">
                <Trans
                  i18nKey="pages.claimsPreviousLeaves.hintList"
                  components={{
                    "mass-benefits-guide-serious-health-condition-link": (
                      <a
                        target="_blank"
                        rel="noopener"
                        href={
                          routes.external.massgov
                            .benefitsGuide_seriousHealthCondition
                        }
                      />
                    ),
                    li: <li />,
                  }}
                />
              </ul>
            </Details>
          </div>
        }
      />
    </QuestionPage>
  );
};

PreviousLeaves.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};
export default withBenefitsApplication(PreviousLeaves);
