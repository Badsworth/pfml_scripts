import AddButton from "./AddButton";
import AmendableConcurrentLeave from "./AmendableConcurrentLeave";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConcurrentLeaveModel from "../../models/ConcurrentLeave";
import { DateTime } from "luxon";
import EmployerClaim from "../../models/EmployerClaim";
import Heading from "../core/Heading";
import React from "react";
import Table from "../core/Table";
import formatDate from "../../utils/formatDate";
import { useTranslation } from "../../locales/i18n";

interface ConcurrentLeaveProps {
  addedConcurrentLeave?: ConcurrentLeaveModel;
  appErrors: AppErrorInfoCollection;
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
    appErrors,
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
        {t("components.employersConcurrentLeave.explanationDetails", {
          context: leaveContext,
          endDate: formatDate(
            DateTime.fromISO(`${claim.leaveStartDate}`)
              .plus({ days: 6 })
              .toString()
          ).short(),
          startDate: formatDate(claim.leaveStartDate).short(),
        })}
      </p>
      <Table className="width-full">
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
              appErrors={appErrors}
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
              appErrors={appErrors}
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
