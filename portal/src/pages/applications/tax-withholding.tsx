import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.is_withholding_tax"];

export const TaxWithholding = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const withholdTax = get(formState, "is_withholding_tax");

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const handleSave = async () => {
    // The below warnings are only returned from a PATCH, not a GET.
    const has_user_not_found_warning =
      appLogic.benefitsApplications.warningsLists[claim.application_id].some(
        (warning) =>
          warning.type === "require_contributing_employer" ||
          warning.rule === "require_non_exempt_employer" ||
          warning.rule === "require_employee"
      );
    const data = {
      is_withholding_tax: withholdTax,
    };
    has_user_not_found_warning
      ? appLogic.benefitsApplications.update(claim.application_id, {
          additional_user_not_found_info: {
            ...claim?.additional_user_not_found_info,
            is_withholding_tax: formState.is_withholding_tax,
          },
        })
      : await appLogic.benefitsApplications.submitTaxWithholdingPreference(
          claim.application_id,
          data
        );
  };

  return (
    <QuestionPage
      continueButtonLabel={t("pages.claimsTaxWithholding.submit")}
      onSave={handleSave}
      title={t("pages.claimsTaxWithholding.title")}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("is_withholding_tax")}
        choices={[
          {
            checked: withholdTax === true,
            label: t("pages.claimsTaxWithholding.choiceYes"),
            value: "true",
          },
          {
            checked: withholdTax === false,
            label: t("pages.claimsTaxWithholding.choiceNo"),
            value: "false",
          },
        ]}
        type="radio"
        label={t("pages.claimsTaxWithholding.sectionLabel")}
        hint={
          <React.Fragment>
            <Trans
              i18nKey="pages.claimsTaxWithholding.explanation"
              components={{
                "tax-professional-link": (
                  <a
                    href={routes.external.massgov.taxGuide}
                    target="_blank"
                    rel="noreferrer noopener"
                  />
                ),
              }}
            />
          </React.Fragment>
        }
      />
      <div className="margin-top-6 margin-bottom-2">
        <Trans
          i18nKey="pages.claimsTaxWithholding.warning"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
          }}
        />
      </div>
    </QuestionPage>
  );
};

export default withBenefitsApplication(TaxWithholding);
