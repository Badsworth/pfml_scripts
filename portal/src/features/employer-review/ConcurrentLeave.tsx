import AddButton from "./AddButton";
import AmendableConcurrentLeave from "./AmendableConcurrentLeave";
import ConcurrentLeaveModel from "../../models/ConcurrentLeave";
import EmployerClaim from "../../models/EmployerClaim";
import Heading from "../../components/core/Heading";
import React from "react";
import Table from "../../components/core/Table";
import { Trans } from "react-i18next";
import dayjs from "dayjs";
import formatDate from "../../utils/formatDate";
import { useTranslation } from "../../locales/i18n";

interface ConcurrentLeaveProps {
  addedConcurrentLeave?: ConcurrentLeaveModel;
  errors: Error[];
  claim: EmployerClaim;
  concurrentLeave?: ConcurrentLeaveModel;
  onAdd: React.MouseEventHandler<HTMLButtonElement>;
  onChange: (
    arg: ConcurrentLeaveModel | { [key: string]: unknown },
    arg2?: string
  ) => void;
  onRemove: (arg: ConcurrentLeaveModel) => void;
}

/**
 * Display a current leave taken by the employee
 * in the Leave Admin claim review page.
 */

const ConcurrentLeave = (props: ConcurrentLeaveProps) => {
  const { t } = useTranslation();
  const {
    addedConcurrentLeave,
    errors,
    claim,
    concurrentLeave,
    onAdd,
    onChange,
    onRemove,
  } = props;

  const leaveContext = claim.isIntermittent
    ? "intermittent"
    : "continuousOrReduced";

  return (
    <React.Fragment>
      <Heading level="3">
        {t("components.employersConcurrentLeave.header")}
      </Heading>
      <p>{t("components.employersConcurrentLeave.explanation")}</p>
      <p>
        <Trans
          i18nKey="components.employersConcurrentLeave.explanationDetails"
          tOptions={{ context: leaveContext }}
          values={{
            endDate: formatDate(
              dayjs(claim.leaveStartDate).add(6, "day").format()
            ).short(),
            startDate: formatDate(claim.leaveStartDate).short(),
          }}
        />
      </p>
      <Table className="width-full" responsive>
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersConcurrentLeave.dateRangeLabel")}
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {concurrentLeave ? (
            <AmendableConcurrentLeave
              errors={errors}
              concurrentLeave={concurrentLeave}
              isAddedByLeaveAdmin={false}
              onChange={onChange}
              onRemove={onRemove}
            />
          ) : (
            <tr>
              <td>{t("shared.noneReported")}</td>
              <td></td>
            </tr>
          )}
          {addedConcurrentLeave && !concurrentLeave && (
            <AmendableConcurrentLeave
              errors={errors}
              concurrentLeave={addedConcurrentLeave}
              isAddedByLeaveAdmin
              onChange={onChange}
              onRemove={onRemove}
            />
          )}
          {!concurrentLeave && !addedConcurrentLeave && (
            <tr>
              <td className="padding-y-2 padding-left-0">
                <AddButton
                  label={t("components.employersConcurrentLeave.addButton")}
                  onClick={onAdd}
                />
              </td>
              <td></td>
            </tr>
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

export default ConcurrentLeave;
