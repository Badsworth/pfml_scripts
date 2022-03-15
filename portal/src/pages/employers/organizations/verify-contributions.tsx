import withWithholding, {
  WithWithholdingProps,
} from "../../../hoc/withWithholding";
import Button from "../../../components/core/Button";
import Details from "../../../components/core/Details";
import InputCurrency from "../../../components/core/InputCurrency";
import Lead from "../../../components/core/Lead";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import formatDateRange from "../../../utils/formatDateRange";
import routes from "../../../routes";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../../hooks/useThrottledHandler";
import { useTranslation } from "../../../locales/i18n";

interface VerifyContributionsProps extends WithWithholdingProps {
  query: { next?: string };
}

export const VerifyContributions = (props: VerifyContributionsProps) => {
  const { appLogic, employer, query, withholding } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    withholdingAmount: "",
  });

  const handleAmountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    const amount = value ? Number(value.replace(/,/g, "")) : 0;
    updateFields({ withholdingAmount: amount });
  };

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    const payload = {
      employer_id: employer.employer_id,
      withholding_amount: formState.withholdingAmount,
      withholding_quarter: withholding.filing_period,
    };

    await appLogic.employers.submitWithholding(payload, query.next);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <Title>
        {t("pages.employersOrganizationsVerifyContributions.title")}
      </Title>
      <Lead>
        <Trans
          i18nKey="pages.employersOrganizationsVerifyContributions.companyNameLabel"
          tOptions={{ company: employer.employer_dba }}
        />
        <br />
        <Trans
          i18nKey="pages.employersOrganizationsVerifyContributions.employerIdNumberLabel"
          tOptions={{ ein: employer.employer_fein }}
        />
      </Lead>
      <Lead>
        <Trans
          i18nKey="pages.employersOrganizationsVerifyContributions.lead"
          components={{
            "mass-tax-connect-link": (
              <a
                href={routes.external.massTaxConnect}
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
          }}
        />
      </Lead>
      <Details
        label={t(
          "pages.employersOrganizationsVerifyContributions.detailsLabel"
        )}
      >
        <Trans
          i18nKey="pages.employersOrganizationsVerifyContributions.detailsList"
          values={{
            date: formatDateRange(withholding.filing_period),
          }}
          components={{
            "mass-tax-connect-link": (
              <a
                href={routes.external.massTaxConnect}
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
            "dor-phone-link": (
              <a href={`tel:${t("shared.departmentOfRevenuePhoneNumber")}`} />
            ),
            ol: <ol className="usa-list" />,
            li: <li />,
          }}
        />
      </Details>
      <InputCurrency
        {...getFunctionalInputProps("withholdingAmount")}
        onChange={handleAmountChange}
        hint={t(
          "pages.employersOrganizationsVerifyContributions.withholdingAmountHint"
        )}
        label={t(
          "pages.employersOrganizationsVerifyContributions.withholdingAmountLabel",
          {
            date: formatDateRange(withholding.filing_period),
          }
        )}
        smallLabel
      />
      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.employersOrganizationsVerifyContributions.submitButton")}
      </Button>
    </form>
  );
};

export default withWithholding(VerifyContributions);
