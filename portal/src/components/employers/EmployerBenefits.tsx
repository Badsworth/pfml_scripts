import AddButton from "./AddButton";
import AmendableEmployerBenefit from "./AmendableEmployerBenefit";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import EmployerBenefit from "../../models/EmployerBenefit";
import Heading from "../Heading";
import React from "react";
import Table from "../Table";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface EmployerBenefitsProps {
  addedBenefits: EmployerBenefit[];
  appErrors: AppErrorInfoCollection;
  employerBenefits?: EmployerBenefit[];
  onAdd: React.MouseEventHandler<HTMLButtonElement>;
  onChange: (...args: any[]) => any;
  onRemove: (...args: any[]) => any;
  shouldShowV2: boolean;
}

/**
 * Display all employer benefits
 * in the Leave Admin claim review page.
 */

const EmployerBenefits = (props: EmployerBenefitsProps) => {
  const { t } = useTranslation();
  const {
    addedBenefits,
    appErrors,
    employerBenefits,
    onAdd,
    onChange,
    onRemove,
    shouldShowV2,
  } = props;
  const limit = 4;

  return (
    <React.Fragment>
      <Heading level="3">
        {t("components.employersEmployerBenefits.header")}
      </Heading>
      <p>
        <Trans
          i18nKey="components.employersEmployerBenefits.caption"
          tOptions={{
            context: shouldShowV2 ? "v2" : "v1",
          }}
          components={{
            "reductions-overview-link": (
              <a
                href={routes.external.massgov.reductionsOverview}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
      <Table className="width-full">
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersEmployerBenefits.dateRangeLabel")}
            </th>
            <th scope="col">
              {t("components.employersEmployerBenefits.benefitTypeLabel")}
            </th>
            <th scope="col">
              {t("components.employersEmployerBenefits.detailsLabel")}
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {employerBenefits.length ? (
            employerBenefits.map((employerBenefit) => (
              <AmendableEmployerBenefit
                appErrors={appErrors}
                isAddedByLeaveAdmin={false}
                employerBenefit={employerBenefit}
                key={employerBenefit.employer_benefit_id}
                onChange={onChange}
                onRemove={onRemove}
                shouldShowV2={shouldShowV2}
              />
            ))
          ) : (
            <tr>
              <td>{t("shared.noneReported")}</td>
              <td></td>
              <td></td>
              <td></td>
            </tr>
          )}
          {shouldShowV2 &&
            addedBenefits.map((addedBenefit) => (
              <AmendableEmployerBenefit
                appErrors={appErrors}
                isAddedByLeaveAdmin
                employerBenefit={addedBenefit}
                key={addedBenefit.employer_benefit_id}
                onChange={onChange}
                onRemove={onRemove}
                shouldShowV2={shouldShowV2}
              />
            ))}
          {shouldShowV2 && (
            <tr>
              <td className="padding-y-2 padding-left-0">
                <AddButton
                  label={t("components.employersEmployerBenefits.addButton", {
                    context:
                      addedBenefits.length === 0 ? "first" : "subsequent",
                  })}
                  onClick={onAdd}
                  disabled={addedBenefits.length >= limit}
                />
              </td>
              <td></td>
              <td></td>
              <td></td>
            </tr>
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

export default EmployerBenefits;
