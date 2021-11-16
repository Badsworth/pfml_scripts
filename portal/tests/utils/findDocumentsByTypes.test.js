import findDocumentsByTypes from "../../src/utils/findDocumentsByTypes";

describe("findDocumentsByTypes", () => {
  const documentsList = [
    { document_type: "identity" },
    { document_type: "certification" },
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
        { document_type: "testType" },
        { document_type: "testType" },
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
      { document_type: "Test Type" },
      { document_type: "test Type" },
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
      { document_type: "Test Type" },
      { document_type: "test Type" },
      { document_type: "test Type 2" },
      { document_type: "Test Type 2" },
    ];
    const documents = findDocumentsByTypes(
      [...documentsList, ...testDocs],
      ["test type", "test type 2"]
    );

    expect(documents).toHaveLength(4);
    expect(documents).toEqual(testDocs);
  });
});
