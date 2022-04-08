import ApiResourceCollection from "src/models/ApiResourceCollection";
import ChangeRequest from "src/models/ChangeRequest";
import ChangeRequestApi from "src/api/ChangeRequestApi";
import { ErrorsLogic } from "./useErrorsLogic";
import { PortalFlow } from "./usePortalFlow";
import useCollectionState from "./useCollectionState";
import { useState } from "react";
import getRelevantIssues from "src/utils/getRelevantIssues";
import { ValidationError } from "src/errors";
import { P } from "@storybook/components";
import TempFile from "src/models/TempFile";
import assert from "assert";

const useChangeRequestLogic = ({
  errorsLogic,
  portalFlow,
}: {
  errorLogic: ErrorsLogic;
  portalFlow: PortalFlow;
}) => {
  const {
    collection: changeRequests,
    setCollection: setChangeRequests,
    addItem: addChangeRequest,
    removeItem: removeChangeRequest,
    updateItem: setChangeRequest,
  } = useCollectionState(
    new ApiResourceCollection<ChangeRequest>("change_request_id")
  );
  const [isLoadingChangeRequests, setIsLoadingChangeRequests] =
    useState<boolean>();
  const [hasLoadedChangeRequests, setHasLoadedChangeRequests] =
    useState<boolean>();
  const changeRequestApi = new ChangeRequestApi();

  const loadAll = async (absenceId: string) => {
    if (isLoadingChangeRequests || hasLoadedChangeRequests) return;

    setIsLoadingChangeRequests(true);
    errorsLogic.clearErrors();

    try {
      const { changeRequests } = await changeRequestApi.getChangeRequests(
        absenceId
      );
      setChangeRequests(changeRequests);
    } catch (error) {
      errorsLogic.catchError(error);
    } finally {
      setIsLoadingChangeRequests(false);
      setHasLoadedChangeRequests(true);
    }
  };

  const create = async (absenceId: string) => {
    errorsLogic.clearErrors();

    try {
      await changeRequestApi.createChangeRequest(absenceId);
      // force reload of change requests next time `loadAll` is called
      setHasLoadedChangeRequests(false);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  const destroy = async (changeRequestId: string) => {
    errorsLogic.clearErrors();

    try {
      const { changeRequest } = await changeRequestApi.deleteChangeRequest(
        changeRequestId
      );

      removeChangeRequest(changeRequest.change_request_id);
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
        await changeRequestApi.updateChangeRequest(changeRequestId, patchData);

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
      const { changeRequest } = await changeRequestApi.submitChangeRequest(
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
    loadAll,
    create,
    destroy,
    update,
    submit,
    attachDocuments,
  };
};

export default useChangeRequestLogic;
