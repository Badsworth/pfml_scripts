import AddButton from "./AddButton";
import AmendableEmployerBenefit from "./AmendableEmployerBenefit";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import EmployerBenefit from "../../models/EmployerBenefit";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

/**
 * Display all employer benefits
 * in the Leave Admin claim review page.
 */

const EmployerBenefits = (props) => {
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
      <ReviewHeading level="2">
        {t("components.employersEmployerBenefits.header")}
      </ReviewHeading>
      <Table className="width-full">
        <caption>
          <p className="text-normal">
            <Trans
              i18nKey="components.employersEmployerBenefits.caption"
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
          <p>{t("components.employersEmployerBenefits.tableName")}</p>
        </caption>
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersEmployerBenefits.dateRangeLabel")}
            </th>
            <th scope="col">
              {t("components.employersEmployerBenefits.benefitTypeLabel")}
            </th>
            <th scope="col" colSpan="2">
              {t("components.employersEmployerBenefits.detailsLabel")}
            </th>
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
              <th scope="row">{t("shared.noneReported")}</th>
              <td colSpan="3" />
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
              <td colSpan="4" className="padding-y-2 padding-left-0">
                <AddButton
                  label={t("components.employersEmployerBenefits.addButton")}
                  onClick={onAdd}
                  disabled={addedBenefits.length >= limit}
                />
              </td>
            </tr>
          )}
        </tbody>
      </Table>
      <p>{t("components.employersEmployerBenefits.commentInstructions")}</p>
    </React.Fragment>
  );
};

EmployerBenefits.propTypes = {
  addedBenefits: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit))
    .isRequired,
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  employerBenefits: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit)),
  onAdd: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  shouldShowV2: PropTypes.bool.isRequired,
};

export default EmployerBenefits;
