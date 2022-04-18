import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import ChangeRequest from "../../src/models/ChangeRequest";
import ChangeRequestsApi from "../../src/api/ChangeRequestsApi";
import { ErrorsLogic } from "./useErrorsLogic";
import { PortalFlow } from "./usePortalFlow";
import TempFile from "src/models/TempFile";
import { ValidationError } from "../../src/errors";
import assert from "assert";
import getRelevantIssues from "../../src/utils/getRelevantIssues";

import useCollectionState from "./useCollectionState";
import { useState } from "react";
const useChangeRequestsLogic = ({
  errorsLogic,
  portalFlow,
}: {
  errorsLogic: ErrorsLogic;
  portalFlow: PortalFlow;
}) => {
  const {
    collection: changeRequests,
    setCollection: setChangeRequests,
    removeItem: removeChangeRequest,
    updateItem: setChangeRequest,
  } = useCollectionState(
    new ApiResourceCollection<ChangeRequest>("change_request_id")
  );
  const [isLoadingChangeRequests, setIsLoadingChangeRequests] =
    useState<boolean>();
  const [hasLoadedChangeRequests, setHasLoadedChangeRequests] =
    useState<boolean>();
  const changeRequestsApi = new ChangeRequestsApi();

  const loadAll = async (absenceId: string) => {
    if (isLoadingChangeRequests || hasLoadedChangeRequests) return;

    setIsLoadingChangeRequests(true);
    errorsLogic.clearErrors();

    try {
      const { changeRequests } = await changeRequestsApi.getChangeRequests(
        absenceId
      );
      setChangeRequests(changeRequests);
      setHasLoadedChangeRequests(true);
    } catch (error) {
      errorsLogic.catchError(error);
    } finally {
      setIsLoadingChangeRequests(false);
    }
  };

  const create = async (absenceId: string) => {
    errorsLogic.clearErrors();

    try {
      await changeRequestsApi.createChangeRequest(absenceId);
      // force reload of change requests next time `loadAll` is called
      setHasLoadedChangeRequests(false);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  const destroy = async (changeRequestId: string) => {
    errorsLogic.clearErrors();

    try {
      await changeRequestsApi.deleteChangeRequest(changeRequestId);

      removeChangeRequest(changeRequestId);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  const update = async (
    changeRequestId: string,
    patchData: Partial<ChangeRequest>
  ) => {
    errorsLogic.clearErrors();

    try {
      const { changeRequest, warnings } =
        await changeRequestsApi.updateChangeRequest(changeRequestId, patchData);

      const issues = getRelevantIssues([], warnings, [portalFlow.page]);

      setChangeRequest(changeRequest);

      if (issues.length) throw new ValidationError(issues);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  const submit = async (changeRequestId: string) => {
    errorsLogic.clearErrors();

    try {
      const { changeRequest } = await changeRequestsApi.submitChangeRequest(
        changeRequestId
      );

      setChangeRequest(changeRequest);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  const attachDocuments = async (
    changeRequestId: string,
    files: TempFile[]
  ) => {
    errorsLogic.clearErrors();

    try {
      // TODO (PORTAL-2023): attach documents
      await assert(changeRequestId && files);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  return {
    changeRequests,
    hasLoadedChangeRequests,
    isLoadingChangeRequests,
    loadAll,
    create,
    destroy,
    update,
    submit,
    attachDocuments,
  };
};

export default useChangeRequestsLogic;
