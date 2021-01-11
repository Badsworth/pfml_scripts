import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Button from "../../components/Button";
import Details from "../../components/Details";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";

export const VerifyBusiness = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    withholdingAmount: "",
  });

  // TODO (EMPLOYER-471): This isn't actually implemented yet, send withholding amount to API
  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.employers.verifyBusiness(formState.withholdingAmount);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      <Title>{t("pages.employersAuthVerifyBusiness.title")}</Title>
      <Lead>
        {t("pages.employersAuthVerifyBusiness.companyNameLabel", {
          company: "Company Name",
        })}
        <br />
        {t("pages.employersAuthVerifyBusiness.employerIdNumberLabel", {
          ein: "XX-XXX-XXXX",
        })}
      </Lead>
      <Lead>
        <Trans
          i18nKey="pages.employersAuthVerifyBusiness.lead"
          components={{
            "mass-tax-connect-link": <a href="" />,
          }}
        />
      </Lead>
      <Details label={t("pages.employersAuthVerifyBusiness.detailsLabel")}>
        <Trans
          i18nKey="pages.employersAuthVerifyBusiness.detailsList"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />
      </Details>
      {/* TODO (EMPLOYER-470): Display date based on GET request for latest filing period */}
      <InputText
        {...getFunctionalInputProps("withholdingAmount")}
        mask="currency"
        hint={t("pages.employersAuthVerifyBusiness.withholdingAmountHint")}
        label={t("pages.employersAuthVerifyBusiness.withholdingAmountLabel", {
          date: "XX-XX-XXXX",
        })}
        smallLabel
      />
      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.employersAuthVerifyBusiness.submitButton")}
      </Button>
    </form>
  );
};

VerifyBusiness.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    employers: PropTypes.shape({
      verifyBusiness: PropTypes.func,
    }),
  }).isRequired,
};

export default VerifyBusiness;
