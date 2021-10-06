/* eslint testing-library/prefer-user-event: 0 */
import Document, { DocumentType } from "../../../../src/models/Document";
import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import ConcurrentLeave from "../../../../src/models/ConcurrentLeave";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import { EmployerBenefitFrequency } from "../../../../src/models/EmployerBenefit";
import EmployerClaim from "../../../../src/models/EmployerClaim";
import LeaveReason from "../../../../src/models/LeaveReason";
import Review from "../../../../src/pages/employers/applications/review";
import { clone } from "lodash";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/hooks/useAppLogic");

const DOCUMENTS = new DocumentCollection([
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-4",
    name: "Medical cert doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-01-02",
    document_type: DocumentType.approvalNotice,
    fineos_document_id: "fineos-id-1",
    name: "Approval notice doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-02-01",
    document_type: DocumentType.certification[LeaveReason.care],
    fineos_document_id: "fineos-id-10",
    name: "Caring cert doc",
  }),
]);

const baseClaimBuilder = new MockEmployerClaimBuilder()
  .completed()
  .reviewable();
const claimWithV1Eform = baseClaimBuilder.eformsV1().create();
const claimWithV2Eform = baseClaimBuilder.eformsV2().create();
const submitClaimReview = jest.fn(() => {
  return Promise.resolve();
});
const goTo = jest.fn(() => {
  return Promise.resolve();
});
const loadDocuments = jest.fn();

const setup = (employerClaimAttrs = claimWithV2Eform, cb) => {
  return renderPage(
    Review,
    {
      addCustomSetup: (appLogic) => {
        appLogic.employers.claim = new EmployerClaim(employerClaimAttrs);
        appLogic.employers.submitClaimReview = submitClaimReview;
        appLogic.portalFlow.goTo = goTo;
        appLogic.employers.loadDocuments = loadDocuments;
        if (cb) {
          cb(appLogic);
        }
      },
    },
    { query: { absence_id: "NTN-111-ABS-01" } }
  );
};

describe("Review", () => {
  it("renders the page for v1 eforms", () => {
    setup(claimWithV1Eform);
    expect(screen.getByText(/Employee information/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Did the employee give you at least 30 days notice about their leave?/
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Employer-sponsored benefits" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Have you approved or denied this leave request?/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Do you have any additional comments or concerns?/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Do you have any reason to suspect this is fraud?/)
    ).toBeInTheDocument();
    expect(screen.getByText(/Leave details/)).toBeInTheDocument();
    expect(screen.getByText(/Leave schedule/)).toBeInTheDocument();
    expect(screen.getByText(/Supporting work details/)).toBeInTheDocument();
    expect(
      screen.queryByText(/Concurrent accrued paid leave/)
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Previous leave/)).not.toBeInTheDocument();
  });

  it("renders the page for v2 eforms", () => {
    setup(claimWithV2Eform);
    expect(screen.getByText(/Employee information/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Did the employee give you at least 30 days notice about their leave?/
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Employer-sponsored benefits" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Have you approved or denied this leave request?/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Do you have any additional comments or concerns?/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Do you have any reason to suspect this is fraud?/)
    ).toBeInTheDocument();
    expect(screen.getByText(/Leave details/)).toBeInTheDocument();
    expect(screen.getByText(/Leave schedule/)).toBeInTheDocument();
    expect(screen.getByText(/Supporting work details/)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Concurrent accrued paid leave" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Previous leave" })
    ).toBeInTheDocument();
  });

  it("renders default view onload with v2 of claim", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();

    // Safeguard to ensure we're passing in all the required data into our test.
    // There shouldn't be any missing content strings.
    expect(
      screen.queryByText(/pages\.employersClaimsReview./i)
    ).not.toBeInTheDocument();
  });

  it("displays organization/employer information", () => {
    setup();
    expect(screen.getByText(/Organization/)).toMatchSnapshot();
    expect(screen.getByText("Employer ID number (EIN)")).toMatchSnapshot();
  });

  it("hides organization name if employer_dba is falsy", () => {
    const noEmployerDba = clone(claimWithV1Eform);
    noEmployerDba.employer_dba = undefined;

    setup(noEmployerDba);

    expect(screen.queryByText(/Organization/)).not.toBeInTheDocument();
    expect(screen.getByText("Employer ID number (EIN)")).toBeInTheDocument();
  });

  it("submits a claim with the correct options", async () => {
    setup();
    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith("NTN-111-ABS-01", {
        comment: expect.any(String),
        employer_benefits: expect.any(Array),
        employer_decision: "Approve", // "Approve" by default
        fraud: undefined, // undefined by default
        hours_worked_per_week: expect.any(Number),
        previous_leaves: expect.any(Array),
        concurrent_leave: null,
        has_amendments: false,
        leave_reason: "Serious Health Condition - Employee",
        uses_second_eform_version: true,
      });
    });
  });

  it("sets payload based on 'comment' input", async () => {
    setup();
    await act(async () => {
      await userEvent.click(screen.getAllByRole("radio", { name: "Yes" })[1]);
      await userEvent.type(
        screen.getByRole("textbox", { name: "Please tell us more." }),
        "my comment"
      );
    });
    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ comment: "my comment" })
      );
    });
  });

  it("sets payload based on 'employer_decision' input", async () => {
    setup();
    userEvent.click(
      screen.getByRole("radio", { name: "Deny (explain below)" })
    );
    userEvent.type(
      screen.getByRole("textbox", {
        name: "Please tell us why you denied this leave request.",
      }),
      "missing data"
    );
    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          employer_decision: "Deny",
          comment: "missing data",
        })
      );
    });
  });

  describe("when leave request is denied", () => {
    it("disables 'No' and selects 'Yes' for 'should_show_comment_box'", () => {
      setup();
      userEvent.click(
        screen.getByRole("radio", { name: "Deny (explain below)" })
      );
      const noFeedbackChoice = screen.getAllByRole("radio", { name: "No" })[1];
      const yesFeedbackChoice = screen.getAllByRole("radio", {
        name: "Yes",
      })[1];

      expect(noFeedbackChoice).toBeDisabled();
      expect(yesFeedbackChoice).toBeChecked();
    });

    describe("and is then approved", () => {
      it("re-enables the 'No' should_show_comment_box choice", () => {
        setup();
        userEvent.click(
          screen.getByRole("radio", { name: "Deny (explain below)" })
        );
        const noFeedbackChoice = screen.getAllByRole("radio", {
          name: "No",
        })[1];

        userEvent.click(screen.getByRole("radio", { name: "Approve" }));
        expect(noFeedbackChoice).toBeEnabled();
      });

      it("selects 'No' for should_show_comment_box if there is no comment", () => {
        setup();
        userEvent.click(
          screen.getByRole("radio", { name: "Deny (explain below)" })
        );
        userEvent.click(screen.getByRole("radio", { name: "Approve" }));
        const noFeedbackChoice = screen.getAllByRole("radio", {
          name: "No",
        })[1];

        expect(noFeedbackChoice).toBeChecked();
      });

      it('selects "Yes" for should_show_comment_box if there is a comment', async () => {
        setup();
        userEvent.click(
          screen.getByRole("radio", { name: "Deny (explain below)" })
        );
        await act(async () => {
          await userEvent.type(
            screen.getByRole("textbox", {
              name: "Please tell us why you denied this leave request.",
            }),
            "hi"
          );
        });
        userEvent.click(screen.getByRole("radio", { name: "Approve" }));
        const yesFeedbackChoice = screen.getAllByRole("radio", {
          name: "Yes",
        })[1];

        expect(yesFeedbackChoice).toBeChecked();
      });
    });

    it("sets payload based on 'fraud' input", async () => {
      setup();
      userEvent.click(
        screen.getByRole("radio", { name: "Yes (explain below)" })
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Please tell us why you believe this is fraudulent.",
        }),
        "fraudster"
      );
      userEvent.click(screen.getByRole("button", { name: "Submit" }));
      await waitFor(() => {
        expect(submitClaimReview).toHaveBeenCalledWith(
          "NTN-111-ABS-01",
          expect.objectContaining({ fraud: "Yes" })
        );
      });
    });

    describe("when fraud is reported", () => {
      it("disables all employee_notice choices", () => {
        setup();
        userEvent.click(
          screen.getByRole("radio", { name: "Yes (explain below)" })
        );
        const employeeNoticeYes = screen.getAllByRole("radio", {
          name: "Yes",
        })[0];
        const employeeNoticeNo = screen.getByRole("radio", {
          name: "No (explain below)",
        });
        expect(employeeNoticeNo).toBeDisabled();
        expect(employeeNoticeYes).toBeDisabled();
      });

      it("disables 'Approve' and selects 'Deny' for employer_decision", () => {
        setup();
        userEvent.click(
          screen.getByRole("radio", { name: "Yes (explain below)" })
        );
        const approveChoice = screen.getByRole("radio", { name: "Approve" });
        const denyChoice = screen.getByRole("radio", {
          name: "Deny (explain below)",
        });
        expect(approveChoice).toBeDisabled();
        expect(denyChoice).toBeChecked();
      });

      it("disables 'No' and selects 'Yes' for should_show_comment_box choice", () => {
        setup();
        userEvent.click(
          screen.getByRole("radio", { name: "Yes (explain below)" })
        );
        const noComment = screen.getAllByRole("radio", { name: "No" })[1];
        const yesComment = screen.getAllByRole("radio", {
          name: "Yes",
        })[1];
        expect(noComment).toBeDisabled();
        expect(yesComment).toBeChecked();
      });

      describe("and then reverted to not fraud", () => {
        it("re-enables all employee_notice choices", () => {
          setup();
          userEvent.click(
            screen.getByRole("radio", { name: "Yes (explain below)" })
          );
          userEvent.click(screen.getAllByRole("radio", { name: "No" })[0]);

          const employeeNoticeYes = screen.getAllByRole("radio", {
            name: "No",
          })[0];
          const employeeNoticeNo = screen.getByRole("radio", {
            name: "No (explain below)",
          });
          expect(employeeNoticeYes).toBeEnabled();
          expect(employeeNoticeNo).toBeEnabled();
        });

        it("re-enables and unselects all employer_decision choices", () => {
          setup();
          userEvent.click(
            screen.getByRole("radio", { name: "Yes (explain below)" })
          );
          userEvent.click(screen.getAllByRole("radio", { name: "No" })[0]);

          const approveChoice = screen.getByRole("radio", { name: "Approve" });
          const denyChoice = screen.getByRole("radio", {
            name: "Deny (explain below)",
          });
          expect(approveChoice).toBeEnabled();
          expect(approveChoice).not.toBeChecked();
          expect(denyChoice).toBeEnabled();
          expect(denyChoice).not.toBeChecked();
        });

        it("selects 'No' for should_show_comment_box if there is no comment", () => {
          setup();
          userEvent.click(
            screen.getByRole("radio", { name: "Yes (explain below)" })
          );
          userEvent.click(screen.getAllByRole("radio", { name: "No" })[0]);

          const noComment = screen.getAllByRole("radio", { name: "No" })[1];
          expect(noComment).toBeChecked();
        });

        it("selects 'Yes' for should_show_comment_box if there is a comment", async () => {
          setup();
          userEvent.click(
            screen.getByRole("radio", { name: "Yes (explain below)" })
          );
          await act(async () => {
            await userEvent.type(
              screen.getByRole("textbox", {
                name: "Please tell us why you believe this is fraudulent.",
              }),
              "comment"
            );
          });
          userEvent.click(screen.getAllByRole("radio", { name: "No" })[0]);

          const yesChoice = screen.getAllByRole("radio", {
            name: "Yes",
          })[1];
          expect(yesChoice).toBeChecked();
        });
      });
    });
  });

  it("sets 'hours_worked_per_week' based on SupportingWorkDetails", async () => {
    setup();
    userEvent.click(screen.getAllByRole("button", { name: "Amend" })[0]);

    userEvent.type(
      screen.getByLabelText(
        /On average, how many hours does the employee work each week\?/
      ),
      "{backspace}{backspace}50"
    );

    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ hours_worked_per_week: 50 })
      );
    });
  });

  it("restores the default hours_worked_per_week if the value in the form is null", async () => {
    setup();
    userEvent.click(screen.getAllByRole("button", { name: "Amend" })[0]);
    userEvent.type(
      screen.getByLabelText(
        /On average, how many hours does the employee work each week\?/
      ),
      "{backspace}{backspace}"
    );
    userEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ hours_worked_per_week: 30 })
      );
    });
  });

  it.todo("sets 'previous_leaves' based on PreviousLeaves");

  it.todo("sets 'employer_benefits' based on EmployerBenefits");

  it("sends concurrent leave if uses_second_eform_version is true", async () => {
    const claimWithConcurrentLeave = baseClaimBuilder
      .eformsV2()
      .concurrentLeave()
      .create();

    setup(claimWithConcurrentLeave);

    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          concurrent_leave: new ConcurrentLeave({
            is_for_current_employer: true,
            leave_start_date: "2021-01-01",
            leave_end_date: "2021-03-01",
          }),
        })
      );
    });
  });

  it("sends amended concurrent leave if uses_second_eform_version is true", async () => {
    const claim = new MockEmployerClaimBuilder()
      .completed()
      .reviewable()
      .eformsV2()
      .concurrentLeave()
      .create();

    setup(claim);
    userEvent.click(screen.getAllByRole("button", { name: "Amend" })[1]);

    const [startMonthInput, endMonthInput] = screen.getAllByRole("textbox", {
      name: "Month",
    });
    const [startDayInput, endDayInput] = screen.getAllByRole("textbox", {
      name: "Day",
    });
    const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
      name: "Year",
    });
    fireEvent.change(startYearInput, { target: { value: "2021" } });
    fireEvent.change(startDayInput, { target: { value: "10" } });
    fireEvent.change(startMonthInput, { target: { value: "10" } });
    fireEvent.change(endYearInput, { target: { value: "2021" } });
    fireEvent.change(endDayInput, { target: { value: "17" } });
    fireEvent.change(endMonthInput, { target: { value: "10" } });

    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          concurrent_leave: new ConcurrentLeave({
            is_for_current_employer: true,
            leave_start_date: "2021-10-10",
            leave_end_date: "2021-10-17",
          }),
        })
      );
    });
  });

  it("does not redirect if is_reviewable is true", () => {
    setup();
    expect(goTo).not.toHaveBeenCalled();
  });

  it("redirects to the status page if is_reviewable is false", () => {
    const falseIsReviewableClaim = new MockEmployerClaimBuilder()
      .completed()
      .reviewable(false)
      .create();

    setup(falseIsReviewableClaim);

    expect(goTo).toHaveBeenCalledWith("/employers/applications/status", {
      absence_id: "NTN-111-ABS-01",
    });
  });

  it("does not redirect to the status page if is_reviewable is null", () => {
    const nullIsReviewableClaim = new MockEmployerClaimBuilder()
      .completed()
      .create();

    setup(nullIsReviewableClaim);

    expect(nullIsReviewableClaim.is_reviewable).toBe(null);
    expect(goTo).not.toHaveBeenCalled();
  });

  it("sets 'has_amendments' to false if nothing is amended", async () => {
    setup();
    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ has_amendments: false })
      );
    });
  });

  it("sets 'has_amendments' to true if benefits are amended", async () => {
    setup();

    userEvent.click(screen.getAllByRole("button", { name: "Amend" })[2]);
    const frequencyDropdown = screen.getByLabelText("Frequency");
    fireEvent.change(frequencyDropdown, {
      target: { value: EmployerBenefitFrequency.weekly },
    });

    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ has_amendments: true })
      );
    });
  });

  it("sets 'has_amendments' to true if benefits are added", async () => {
    setup(claimWithV2Eform);
    userEvent.click(screen.getByText("Add an employer-sponsored benefit"));

    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ has_amendments: true })
      );
    });
  });

  it("sets 'has_amendments' to true if previous leaves are amended", async () => {
    setup(claimWithV2Eform);
    userEvent.click(screen.getAllByRole("button", { name: "Amend" })[1]);

    const [startMonthInput, endMonthInput] = screen.getAllByRole("textbox", {
      name: "Month",
    });
    fireEvent.change(startMonthInput, { target: { value: "05" } });
    fireEvent.change(endMonthInput, { target: { value: "06" } });

    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ has_amendments: true })
      );
    });
  });

  it("sets 'has_amendments' to true if previous leaves are added", async () => {
    setup(claimWithV2Eform);

    userEvent.click(
      screen.getByRole("button", { name: "Add a previous leave" })
    );
    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({ has_amendments: true })
      );
    });
  });

  it("sets 'has_amendments' to true if hours are amended", async () => {
    setup();
    userEvent.click(screen.getAllByRole("button", { name: "Amend" })[0]);
    const inputElement = screen.getByLabelText(
      /On average, how many hours does the employee work each week\?/
    );
    userEvent.type(inputElement, "{backspace}{backspace}60");
    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          has_amendments: true,
          hours_worked_per_week: 60,
        })
      );
    });
  });

  it("only calls preventDefault when pressing enter in text input", () => {
    setup();
    userEvent.click(screen.getAllByRole("button", { name: "Amend" })[0]);
    const textInput = screen.getByLabelText(
      /On average, how many hours does the employee work each week\?/
    );

    const fired = fireEvent.keyDown(textInput, {
      keyCode: 13,
    });
    expect(fired).toBe(false);

    const regularKeyFired = fireEvent.keyDown(textInput, {
      keyCode: 65,
    });

    expect(regularKeyFired).toBe(true);
  });

  it("doesn't call preventDefault() when pressing enter on submit button", async () => {
    setup();
    const mockPreventDefault = jest.fn();
    fireEvent.keyDown(screen.getByRole("button", { name: "Submit" }), {
      key: "Enter",
      charCode: 13,
      preventDefault: mockPreventDefault,
    });
    await waitFor(() => {
      expect(mockPreventDefault).not.toHaveBeenCalled();
    });
  });

  describe("Documents", () => {
    it("loads the documents while documents are undefined", () => {
      setup();
      expect(loadDocuments).toHaveBeenCalledWith("NTN-111-ABS-01");
    });

    describe("when the claim is a caring leave", () => {
      function render() {
        const caringLeaveClaim = clone(claimWithV2Eform);
        caringLeaveClaim.leave_details.reason = "Care for a Family Member";
        const cb = (appLogic) => {
          appLogic.employers.documents = DOCUMENTS;
        };
        setup(caringLeaveClaim, cb);
      }

      it("does not load the documents while documents is loaded ", () => {
        render();
        expect(loadDocuments).not.toHaveBeenCalled();
      });

      it("shows medical cert and caring cert", () => {
        render();
        expect(
          screen.getAllByText(/Your employee's certification document/)
        ).toHaveLength(2);
      });
    });
  });

  describe("Caring Leave", () => {
    beforeEach(() => {
      const caringLeaveClaim = new MockEmployerClaimBuilder()
        .eformsV2()
        .completed()
        .caringLeaveReason()
        .reviewable()
        .create();

      setup(caringLeaveClaim);
    });

    it("submits a caring leave claim with the correct options", async () => {
      userEvent.click(screen.getByRole("button", { name: "Submit" }));
      await waitFor(() => {
        expect(submitClaimReview).toHaveBeenCalledWith("NTN-111-ABS-01", {
          believe_relationship_accurate: undefined, // undefined by default
          comment: expect.any(String),
          employer_benefits: expect.any(Array),
          employer_decision: "Approve", // "Approve" by default
          fraud: undefined, // undefined by default
          hours_worked_per_week: expect.any(Number),
          previous_leaves: expect.any(Array),
          concurrent_leave: null,
          has_amendments: false,
          uses_second_eform_version: true,
          relationship_inaccurate_reason: expect.any(String),
          leave_reason: "Care for a Family Member",
        });
      });
    });

    it("disables submit button when LA indicates the relationship is inaccurate and no relationship comment", () => {
      userEvent.click(
        screen.getByRole("radio", { name: "No (comment required)" })
      );
      expect(screen.getByRole("button", { name: "Submit" })).toBeDisabled();
    });

    it("submits has_amendments as false when LA indicates the relationship is inaccurate", async () => {
      userEvent.click(
        screen.getByRole("radio", { name: "No (comment required)" })
      );
      userEvent.type(
        screen.getByRole("textbox", {
          name: "Tell us why you think this relationship is inaccurate.",
        }),
        "miau"
      );

      userEvent.click(screen.getByRole("button", { name: "Submit" }));
      await waitFor(() => {
        expect(submitClaimReview).toHaveBeenCalledWith(
          "NTN-111-ABS-01",
          expect.objectContaining({
            has_amendments: false,
            uses_second_eform_version: true,
            believe_relationship_accurate: "No",
          })
        );
      });
    });
  });
});
