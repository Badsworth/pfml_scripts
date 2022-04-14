import ChangeRequest, {
  ChangeRequestType,
} from "../../../src/models/ChangeRequest";
import machineConfigs, { guards } from "../../../src/flows";
import { createMachine } from "xstate";
import ClaimDetail from "../../../src/models/ClaimDetail";
import LeaveReason from "../../../src/models/LeaveReason";
import routes from "../../../src/routes";

describe("modification flow", () => {
  const getNextRoute = (
    currentRoute,
    event,
    { claimDetail, changeRequest }
  ) => {
    return createMachine(machineConfigs, { guards })
      .withContext({ claimDetail, changeRequest })
      .transition(currentRoute, event)
      .value.toString();
  };

  it("routes to modify/type when continuing from modify/index", () => {
    expect(
      getNextRoute(routes.applications.modify.index, "CONTINUE", {})
    ).toEqual(routes.applications.modify.type);
  });

  describe("when continuing from modify/type", () => {
    const event = "CONTINUE";
    const currentRoute = routes.applications.modify.type;

    it("routes to upload/pregnancy-cert when change request is an extension and claim is pregnancy", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.pregnancy,
            absence_period_end_date: "2022-05-01",
          },
        ],
      });

      const changeRequest = new ChangeRequest({
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-06-01",
      });

      expect(
        getNextRoute(currentRoute, event, { claimDetail, changeRequest })
      ).toEqual(routes.applications.upload.modify.pregnancyCertification);
    });

    it("routes to upload/caring-cert when change request is an extension and claim is pregnancy", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.care,
            absence_period_end_date: "2022-05-01",
          },
        ],
      });

      const changeRequest = new ChangeRequest({
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-06-01",
      });

      expect(
        getNextRoute(currentRoute, event, { claimDetail, changeRequest })
      ).toEqual(routes.applications.upload.modify.caringCertification);
    });

    it("routes to upload/medical-cert when change request is an extension and claim is pregnancy", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.medical,
            absence_period_end_date: "2022-05-01",
          },
        ],
      });

      const changeRequest = new ChangeRequest({
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-06-01",
      });

      expect(
        getNextRoute(currentRoute, event, { claimDetail, changeRequest })
      ).toEqual(routes.applications.upload.modify.medicalCertification);
    });

    it("routes to modify/review when change request is not extension", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.pregnancy,
            absence_period_end_date: "2022-05-01",
          },
        ],
      });

      const changeRequest = new ChangeRequest({
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-04-01",
      });

      expect(
        getNextRoute(currentRoute, event, { claimDetail, changeRequest })
      ).toEqual(routes.applications.modify.review);
    });

    it("routes to modify/review when claim is bonding", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.bonding,
            absence_period_end_date: "2022-05-01",
          },
        ],
      });

      const changeRequest = new ChangeRequest({
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-06-01",
      });

      expect(
        getNextRoute(currentRoute, event, { claimDetail, changeRequest })
      ).toEqual(routes.applications.modify.review);
    });
  });

  describe("when continuing from modify/review", () => {
    const currentRoute = routes.applications.modify.review;
    const event = "CONTINUE";
    it("routes to modify/success when change request is extending", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.pregnancy,
            absence_period_end_date: "2022-05-01",
          },
        ],
      });

      const changeRequest = new ChangeRequest({
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-06-01",
      });

      expect(
        getNextRoute(currentRoute, event, { claimDetail, changeRequest })
      ).toEqual(routes.applications.modify.success);
    });

    it("routes to claim/status when change request is not extending", () => {
      const claimDetail = new ClaimDetail({
        absence_periods: [
          {
            reason: LeaveReason.pregnancy,
            absence_period_end_date: "2022-05-01",
          },
        ],
      });

      const changeRequest = new ChangeRequest({
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-04-01",
      });

      expect(
        getNextRoute(currentRoute, event, { claimDetail, changeRequest })
      ).toEqual(routes.applications.status.claim);
    });
  });

  describe("when continuing from upload pages", () => {
    it.each(
      [
        routes.applications.upload.modify.medicalCertification,
        routes.applications.upload.modify.pregnancyCertification,
        routes.applications.upload.modify.caringCertification,
      ],
      ("routes to modify/review",
      (currentRoute) => {
        expect(getNextRoute(currentRoute, "CONTINUE", {})).toEqual(
          routes.applications.modify.review
        );
      })
    );
  });
});
