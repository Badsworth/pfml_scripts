import AddButton from "./AddButton";
import AmendableConcurrentLeave from "./AmendableConcurrentLeave";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConcurrentLeaveModel from "../../models/ConcurrentLeave";
import Heading from "../Heading";
import React from "react";
import Table from "../Table";
import { useTranslation } from "../../locales/i18n";

interface ConcurrentLeaveProps {
  addedConcurrentLeave?: ConcurrentLeaveModel;
  appErrors: AppErrorInfoCollection;
  concurrentLeave?: ConcurrentLeaveModel;
  onAdd: React.MouseEventHandler<HTMLButtonElement>;
  onChange: (
    arg: ConcurrentLeaveModel | Record<string, unknown>,
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
    concurrentLeave,
    onAdd,
    onChange,
    onRemove,
  } = props;

  return (
    <React.Fragment>
      <Heading level="3">
        {t("components.employersConcurrentLeave.header")}
      </Heading>
      <p>{t("components.employersConcurrentLeave.explanation")}</p>
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
