import BenefitsApplication from "../../src/models/BenefitsApplication";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";
import withClaimDocuments from "../../src/hoc/withClaimDocuments";

jest.mock("../../src/hooks/useAppLogic");

describe("withClaimDocuments", () => {
  let appLogic, wrapper;
  const application_id = "12345";
  const claim = new BenefitsApplication({ application_id });

  const PageComponent = () => <div />;
  const WrappedComponent = withClaimDocuments(PageComponent);

  function render() {
    act(() => {
      wrapper = mount(<WrappedComponent appLogic={appLogic} claim={claim} />);
    });
  }

  beforeEach(() => {
    appLogic = useAppLogic();
  });

  it("loads documents", () => {
    render();
    expect(appLogic.documents.loadAll).toHaveBeenCalledTimes(1);
  });

  it("does not load documents if there are already loaded documents", () => {
    jest
      .spyOn(appLogic.documents, "hasLoadedClaimDocuments")
      .mockReturnValue(true);
    render();
    expect(appLogic.documents.loadAll).not.toHaveBeenCalled();
  });

  it("does not load documents if user has not yet loaded", () => {
    appLogic.user = appLogic.users.user = null;
    render();
    expect(appLogic.benefitsApplications.loadAll).not.toHaveBeenCalled();
  });

  it("does not load documents when documents are already loaded", () => {
    appLogic.documents.hasLoadedClaimDocuments.mockReturnValueOnce(true);
    render();
    expect(appLogic.documents.loadAll).not.toHaveBeenCalled();
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
