import Document from "../../src/models/Document";
import findDocumentsByTypes from "../../src/utils/findDocumentsByTypes";

describe("findDocumentsByTypes", () => {
  const documentsList = [
    new Document({ document_type: "identity" }),
    new Document({ document_type: "certification" }),
  ];
  describe("when no documents are found", () => {
    it("returns an empty array", () => {
      const documents = findDocumentsByTypes(documentsList, ["testType"]);

      expect(documents).toEqual([]);
    });
  });

  describe("when the documents list has multiple matching documents", () => {
    it("returns an array with all of the matching documents", () => {
      const testDocs = [
        new Document({ document_type: "testType" }),
        new Document({ document_type: "testType" }),
      ];
      const documents = findDocumentsByTypes(
        [...documentsList, ...testDocs],
        ["testType"]
      );

      expect(documents).toHaveLength(2);
      expect(documents).toEqual(testDocs);
    });
  });

  describe("when the documents list is empty", () => {
    it("returns an empty array", () => {
      const documents = findDocumentsByTypes([], ["testType"]);
      expect(documents).toEqual([]);
    });
  });

  it("returns matching documents even if casing of document_type is different", () => {
    const testDocs = [
      new Document({ document_type: "Test Type" }),
      new Document({ document_type: "test Type" }),
    ];
    const documents = findDocumentsByTypes(
      [...documentsList, ...testDocs],
      ["test type"]
    );

    expect(documents).toHaveLength(2);
    expect(documents).toEqual(testDocs);
  });

  it("returns matching documents when there are multiple document types", () => {
    const testDocs = [
      new Document({ document_type: "Test Type" }),
      new Document({ document_type: "test Type" }),
      new Document({ document_type: "test Type 2" }),
      new Document({ document_type: "Test Type 2" }),
    ];
    const documents = findDocumentsByTypes(
      [...documentsList, ...testDocs],
      ["test type", "test type 2"]
    );

    expect(documents).toHaveLength(4);
    expect(documents).toEqual(testDocs);
  });
});
