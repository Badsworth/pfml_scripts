import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Button from "../../components/Button";
import Details from "../../components/Details";
import InputNumber from "../../components/InputNumber";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import User from "../../models/User";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

export const VerifyBusiness = (props) => {
  const { appLogic, query, user } = props;
  const { t } = useTranslation();

  if (!isFeatureEnabled("employerShowVerificationPages")) {
    appLogic.portalFlow.goTo(routes.employers.dashboard);
  }

  const employer = user.user_leave_administrators.find((employer) => {
    return employer.employer_id === query.employer_id;
  });

  const { formState, updateFields } = useFormState({
    withholdingAmount: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    const withholdingAmount = parseFloat(
      formState.withholdingAmount.replace(/,/g, "")
    );

    const payload = {
      employer_id: query.employer_id,
      withholding_amount: withholdingAmount,
      withholding_quarter: "2020-10-10", // TODO (EMPLOYER-470): Change based on actual variable
    };

    await appLogic.employers.submitWithholding(payload, query.next);
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
        <Trans
          i18nKey="pages.employersAuthVerifyBusiness.companyNameLabel"
          tOptions={{ company: employer.employer_dba }}
        />
        <br />
        <Trans
          i18nKey="pages.employersAuthVerifyBusiness.employerIdNumberLabel"
          tOptions={{ ein: employer.employer_fein }}
        />
      </Lead>
      <Lead>
        <Trans
          i18nKey="pages.employersAuthVerifyBusiness.lead"
          components={{
            "mass-tax-connect-link": (
              <a
                href={routes.external.massTaxConnect}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </Lead>
      <Details label={t("pages.employersAuthVerifyBusiness.detailsLabel")}>
        <Trans
          i18nKey="pages.employersAuthVerifyBusiness.detailsList"
          components={{
            "mass-tax-connect-link": (
              <a
                href={routes.external.massTaxConnect}
                target="_blank"
                rel="noopener"
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
      {/* TODO (EMPLOYER-470): Display date based on GET request for latest filing period */}
      <InputNumber
        {...getFunctionalInputProps("withholdingAmount")}
        mask="currency"
        hint={t("pages.employersAuthVerifyBusiness.withholdingAmountHint")}
        label={t("pages.employersAuthVerifyBusiness.withholdingAmountLabel", {
          date: "{DD-MMM-YYYY}",
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
      submitWithholding: PropTypes.func.isRequired,
    }),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    employer_id: PropTypes.string.isRequired,
    next: PropTypes.string,
  }).isRequired,
  user: PropTypes.instanceOf(User),
};

export default withUser(VerifyBusiness);
