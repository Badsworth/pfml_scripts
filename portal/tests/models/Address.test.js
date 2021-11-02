import Address from "../../src/models/Address";

describe(Address, () => {
  describe("#toString", () => {
    it("converts Address to a string value", () => {
      expect(
        new Address({
          line_1: "Address line 1",
          line_2: "Address line 2",
          city: "City",
          state: "State",
          zip: "000000",
        }).toString()
      ).toMatchInlineSnapshot(
        `"Address line 1 Address line 2, City State 000000"`
      );
    });

    it("returns empty string will all properties are null", () => {
      expect(new Address().toString()).toMatchInlineSnapshot(`","`);
    });

    it("returns just the address lines when no city, state, or zip is set", () => {
      expect(
        new Address({
          line_1: "Address line 1",
          line_2: "Address line 2",
        }).toString()
      ).toMatchInlineSnapshot(`"Address line 1 Address line 2"`);
    });

    it("does not return address line 2 when it is not set", () => {
      expect(
        new Address({
          line_1: "Address line 1",
          city: "City",
          state: "State",
          zip: "000000",
        }).toString()
      ).toMatchInlineSnapshot(`"Address line 1, City State 000000"`);
    });

    it("does not return line 1 or 2 when it's not set", () => {
      expect(
        new Address({
          city: "City",
          state: "State",
          zip: "000000",
        }).toString()
      ).toMatchInlineSnapshot(`"City State 000000"`);
    });
  });
});
