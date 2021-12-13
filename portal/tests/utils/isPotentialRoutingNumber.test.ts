import { isPotentialRoutingNumber } from "src/utils/isPotentialRoutingNumber";

describe("isPotentialRoutingNumber", () => {
  it("returns false when we expect", () => {
    let result = true;
    result = isPotentialRoutingNumber("1");
    expect(result).toEqual(false);
    result = isPotentialRoutingNumber("123456789");
    expect(result).toEqual(false);
  });

  it("returns true when we expect (with routing-similar numbers)", () => {
    let result = false;
    result = isPotentialRoutingNumber("011000138"); // known BofA routing number
    expect(result).toEqual(true);
    result = isPotentialRoutingNumber("026009593"); // known BofA routing number
    expect(result).toEqual(true);
    result = isPotentialRoutingNumber("121000358");
    expect(result).toEqual(true);
  });
});
