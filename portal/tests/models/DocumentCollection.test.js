import DocumentCollection from "../../src/models/DocumentCollection";

describe("DocumentCollection", () => {
  describe("#filterByApplication", () => {
    it("returns only Documents associated with the given application", () => {
      const applicationADocument1 = {
        application_id: "a",
        fineos_document_id: "a_1",
      };
      const applicationADocument2 = {
        application_id: "a",
        fineos_document_id: "a_2",
      };
      const applicationBDocument1 = {
        application_id: "b",
        fineos_document_id: "b_1",
      };

      const collection = new DocumentCollection([
        applicationADocument1,
        applicationADocument2,
        applicationBDocument1,
      ]);

      expect(collection.filterByApplication("a")).toEqual([
        applicationADocument1,
        applicationADocument2,
      ]);
      expect(collection.filterByApplication("b")).toEqual([
        applicationBDocument1,
      ]);
    });
  });
});
