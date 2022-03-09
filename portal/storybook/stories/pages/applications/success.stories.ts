import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import dayjs from "dayjs";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const monthToAdd = 1; // workaround for https://github.com/storybookjs/storybook/issues/12208
const futureDate = dayjs().add(monthToAdd, "month").format("YYYY-MM-DD");

const mockClaims = {
  "Medical (Not pregnant)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2022-02-15" })
    .medicalLeaveReason()
    .absenceId()
    .create(),
  "Medical (Pregnant)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2022-02-15" })
    .medicalLeaveReason()
    .pregnant()
    .absenceId()
    .create(),
  "Medical (Pregnant, applying in advance)":
    new MockBenefitsApplicationBuilder()
      .continuous({ start_date: futureDate })
      .medicalLeaveReason()
      .pregnant()
      .absenceId()
      .create(),
  "Family (Bonding Newborn)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2022-02-15" })
    .bondingBirthLeaveReason()
    .absenceId()
    .create(),
  "Family (Bonding Future Newborn)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: futureDate })
    .hasFutureChild()
    .bondingBirthLeaveReason(futureDate)
    .absenceId()
    .create(),
  "Family (Bonding Adoption)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2022-02-15" })
    .bondingAdoptionLeaveReason()
    .absenceId()
    .create(),
  "Family (Bonding Future Adoption)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: futureDate })
    .hasFutureChild()
    .bondingAdoptionLeaveReason(futureDate)
    .absenceId()
    .create(),
  "Caring Leave": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2022-02-15" })
    .caringLeaveReason()
    .absenceId()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory("success", mockClaims);
export default config;
export const Default = DefaultStory;
