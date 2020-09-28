import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import withClaimDocuments from "../../src/hoc/withClaimDocuments";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaimDocuments", () => {
  let appLogic, application_id, wrapper;

  const PageComponent = () => <div />;
  const WrappedComponent = withClaimDocuments(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(
        <WrappedComponent
          appLogic={appLogic}
          query={{ claim_id: application_id }}
        />
      );
    });
  }

  beforeEach(() => {
    appLogic = useAppLogic();
    application_id = "12345";
  });

  it("loads documents", () => {
    render();
    expect(appLogic.documents.load).toHaveBeenCalledTimes(1);
  });

  it("does not load documents if there is an error", () => {
    appLogic.appErrors = new AppErrorInfoCollection([new AppErrorInfo()]);
    render();
    expect(appLogic.documents.load).not.toHaveBeenCalled();
  });

  it("does not load documents if user has not yet loaded", () => {
    appLogic.user = appLogic.users.user = null;
    render();
    expect(appLogic.claims.load).not.toHaveBeenCalled();
  });

  it("does not load documents when documents are already loaded", () => {
    appLogic.documents.hasLoadedClaimDocuments.mockReturnValueOnce(true);
    render();
    expect(appLogic.documents.load).not.toHaveBeenCalled();
  });

  it("sets the 'documents' prop on the passed component to the loaded documents", () => {
    const loadedDocuments = new DocumentCollection([
      new Document({ application_id, fineos_document_id: 1 }),
      new Document({ application_id, fineos_document_id: 2 }),
      new Document({ application_id, fineos_document_id: 3 }),
      new Document({
        application_id: "something different",
        fineos_document_id: 4,
      }),
    ]);
    const filterDocuments = loadedDocuments.filterByApplication(application_id);
    appLogic.documents.documents = loadedDocuments;
    render();
    expect(wrapper.find(PageComponent).prop("documents")[0]).toBeInstanceOf(
      Document
    );
    expect(wrapper.find(PageComponent).prop("documents")).toEqual(
      filterDocuments
    );
  });
});
