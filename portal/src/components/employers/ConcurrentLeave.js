import AddButton from "./AddButton";
import AmendableConcurrentLeave from "./AmendableConcurrentLeave";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConcurrentLeaveModel from "../../models/ConcurrentLeave";
import Heading from "../Heading";
import PropTypes from "prop-types";
import React from "react";
import Table from "../Table";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a current leave taken by the employee
 * in the Leave Admin claim review page.
 */

const ConcurrentLeave = (props) => {
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
      <Heading id="concurrent-leave" level="3">
        {t("components.employersConcurrentLeave.header")}
      </Heading>
      <p>{t("components.employersConcurrentLeave.explanation")}</p>
      <Table aria-labelledby="concurrent-leave" className="width-full">
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

ConcurrentLeave.propTypes = {
  addedConcurrentLeave: PropTypes.instanceOf(ConcurrentLeaveModel),
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  concurrentLeave: PropTypes.instanceOf(ConcurrentLeaveModel),
  onAdd: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
};

export default ConcurrentLeave;
