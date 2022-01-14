import { getMaxBenefitAmount } from "../../src/utils/getMaxBenefitAmount";

describe("getMaxBenefitAmount", () => {
  afterAll(() => {
    jest.useRealTimers();
  });
  it("Customizes by current year", () => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date(2022, 1, 1));

    expect(getMaxBenefitAmount()).toEqual(1084);

    jest.useFakeTimers();
    jest.setSystemTime(new Date(2021, 1, 1));

    expect(getMaxBenefitAmount()).toEqual(850);
  });
});
