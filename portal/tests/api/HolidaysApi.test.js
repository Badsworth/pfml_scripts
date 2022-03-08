import { mockAuth, mockFetch } from "../test-utils";
import HolidaysApi from "../../src/api/HolidaysApi";

jest.mock("../../src/services/tracker");

describe("HolidaysApi", () => {
  beforeAll(() => {
    mockAuth();
  });

  const startDate = "2022-01-01";
  const endDate = "2022-12-31";

  it("makes request to holidays API with start and end date", async () => {
    mockFetch();

    const holidaysApi = new HolidaysApi();
    await holidaysApi.getHolidays(startDate, endDate);

    expect(global.fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/holidays/search`,
      expect.objectContaining({
        headers: expect.any(Object),
        method: "POST",
        body: JSON.stringify({
          terms: { start_date: startDate, end_date: endDate },
        }),
      })
    );
  });

  it("returns the holidays", async () => {
    const mockResponseData = [
      { name: "Memorial Day", date: "2022-05-30" },
      { name: "Independance Day", date: "2022-07-04" },
    ];

    mockFetch({
      response: {
        data: mockResponseData,
      },
    });

    const holidaysApi = new HolidaysApi();
    const holidays = await holidaysApi.getHolidays(startDate, endDate);

    expect(holidays[0].name).toBe("Memorial Day");
    expect(holidays[0].date).toBe("2022-05-30");
  });
});
