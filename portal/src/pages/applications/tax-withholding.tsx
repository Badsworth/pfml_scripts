import { get, pick } from "lodash";
import { AppLogic } from "../../hooks/useAppLogic";
import BackButton from "../../components/BackButton";
import BenefitsApplication from "../../models/BenefitsApplication";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import React from "react";
import ThrottledButton from "../../components/ThrottledButton";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.is_withholding_tax"];

interface TaxWithholdingProps {
  claim: BenefitsApplication;
  query: {
    claim_id?: string;
  };
  appLogic: AppLogic;
}

export const TaxWithholding = (props: TaxWithholdingProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const withholdTax = get(formState, "is_withholding_tax");

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleClick = async () => {
    const data = {
      withhold_taxes: withholdTax,
    };
    await appLogic.benefitsApplications.submitTaxWithholdingPreference(
      claim.application_id,
      data
    );
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleClick} className="usa-form" method="post">
        <Title small>{t("pages.claimsTaxWithholding.title")}</Title>
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
        <ThrottledButton
          className="margin-top-4"
          onClick={handleClick}
          type="submit"
        >
          {t("pages.claimsTaxWithholding.submit")}
        </ThrottledButton>
      </form>
    </React.Fragment>
  );
};

export default withBenefitsApplication(TaxWithholding);
