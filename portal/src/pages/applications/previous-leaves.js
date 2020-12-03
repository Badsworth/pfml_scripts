import Claim from "../../models/Claim";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import pick from "lodash/pick";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.temp.has_previous_leaves"];

export const PreviousLeaves = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

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
        {...getFunctionalInputProps("temp.has_previous_leaves")}
        choices={[
          {
            checked: formState.temp.has_previous_leaves === true,
            label: t("pages.claimsPreviousLeaves.choiceYes"),
            value: "true",
          },
          {
            checked: formState.temp.has_previous_leaves === false,
            label: t("pages.claimsPreviousLeaves.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsPreviousLeaves.sectionLabel")}
        type="radio"
        hint={
          <div>
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
            />
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
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};
export default withClaim(PreviousLeaves);
