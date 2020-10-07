import { MockClaimBuilder, renderWithAppLogic } from "../test-utils";
import ApplicationCard from "../../src/components/ApplicationCard";
import Claim from "../../src/models/Claim";

describe("ApplicationCard", () => {
  let wrapper;

  const render = (claimAttrs = {}) => {
    ({ wrapper } = renderWithAppLogic(ApplicationCard, {
      diveLevels: 2,
      props: { claim: new Claim(claimAttrs), number: 2 },
      hasUploadedDocument: true,
    }));
  };

  it("renders a card for the given application", () => {
    render(new MockClaimBuilder().create());

    expect(wrapper).toMatchSnapshot();
  });

  it("renders Continuous leave period date range", () => {
    render(new MockClaimBuilder().continuous().create());

    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Continuous leave"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("1/1/2021 – 6/1/2021");
  });

  it("renders Reduced Schedule leave period date range", () => {
    render(new MockClaimBuilder().reducedSchedule().create());

    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Reduced leave schedule"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("2/1/2021 – 7/1/2021");
  });

  it("renders Intermittent leave period date range", () => {
    render(new MockClaimBuilder().intermittent().create());

    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Intermittent leave"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("2/1/2021 – 7/1/2021");
  });

  describe("when the claim status is Submitted", () => {
    const submittedClaim = new MockClaimBuilder().submitted().create();
    beforeEach(() => {
      render(submittedClaim);
    });

    it("includes a link to edit the claim", () => {
      expect(wrapper.find("ButtonLink")).toHaveLength(1);
    });

    it("uses the Case ID as the main heading", () => {
      expect(wrapper.find("Heading[level='2']").children().text()).toBe(
        submittedClaim.fineos_absence_id
      );
    });
  });

  describe("when the claim status is Completed", () => {
    beforeEach(() => {
      render(new MockClaimBuilder().completed().create());
    });

    it("does not include a link to edit the claim", () => {
      expect(wrapper.find("ButtonLink")).toHaveLength(0);
    });
  });
});
