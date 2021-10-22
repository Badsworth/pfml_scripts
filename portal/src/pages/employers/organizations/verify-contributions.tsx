import { AppLogic } from "../../../hooks/useAppLogic";
import Button from "../../../components/Button";
import Details from "../../../components/Details";
import InputCurrency from "../../../components/InputCurrency";
import Lead from "../../../components/Lead";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import Withholding from "../../../models/Withholding";
import formatDateRange from "../../../utils/formatDateRange";
import routes from "../../../routes";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../../hooks/useThrottledHandler";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";
import withWithholding from "../../../hoc/withWithholding";

interface VerifyContributionsProps {
  appLogic: AppLogic;
  query: {
    employer_id: string;
    next?: string;
  };
  withholding: Withholding;
}

export const VerifyContributions = (props: VerifyContributionsProps) => {
  const { appLogic, query, withholding } = props;
  const {
    users: { user },
  } = appLogic;
  const { t } = useTranslation();
  const employer = user.user_leave_administrators.find((employer) => {
    return employer.employer_id === query.employer_id;
  });

  const { formState, updateFields } = useFormState({
    withholdingAmount: 0,
  });

  const handleAmountChange = (event) => {
    const value = event.target.value;
    const amount = value ? Number(value.replace(/,/g, "")) : 0;
    updateFields({ withholdingAmount: amount });
  };

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    const payload = {
      employer_id: query.employer_id,
      withholding_amount: formState.withholdingAmount,
      withholding_quarter: withholding.filing_period,
    };

    await appLogic.employers.submitWithholding(payload, query.next);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
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
            "recent-filing-periods-link": (
              <a
                href={routes.external.massgov.preparingToVerifyEmployer}
                target="_blank"
                rel="noreferrer noopener"
              />
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

export default withUser(withWithholding(VerifyContributions));
