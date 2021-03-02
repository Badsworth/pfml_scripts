import { initializeI18n } from "../../src/locales/i18n";

describe("i18n formatters", () => {
  it("formats currency values", async () => {
    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          dollarAmount: "{{amount, currency}}",
        },
      },
    });

    expect(t("dollarAmount", { amount: 1000 })).toBe("$1,000.00");
  });

  it("formats hour and minute durations", async () => {
    const t = await initializeI18n("en-US", {
      "en-US": {
        translation: {
          hoursMinutesDuration: "{{minutes, hoursMinutesDuration}}",
        },
      },
    });

    expect(t("hoursMinutesDuration", { minutes: 475 })).toBe("7h 55m");
    expect(t("hoursMinutesDuration", { minutes: 45 })).toBe("0h 45m");
    expect(t("hoursMinutesDuration", { minutes: 0})).toBe("0h");
  });
});
