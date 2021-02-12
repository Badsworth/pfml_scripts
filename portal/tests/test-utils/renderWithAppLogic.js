import Document, { DocumentType } from "../../src/models/Document";
import { mount, shallow } from "enzyme";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import EmployerClaim from "../../src/models/EmployerClaim";
import React from "react";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import merge from "lodash/merge";
import testHook from "./testHook";
import times from "lodash/times";
import useAppLogic from "../../src/hooks/useAppLogic";

/**
 * Render a component, automatically setting its appLogic and query props
 * @example const { appLogic, wrapper } = renderWithAppLogic(MyPage)
 * @param {React.Component} PageComponent - the component you want to render
 * @param {object} [options]
 * @param {object} [options.claimAttrs] - Additional attributes to set on the Claim
 * @param {number} [options.diveLevels] - number of levels to dive before returning the enzyme wrapper.
 *    This is needed to return the desired component when the component is wrapped in higher-order components.
 *    Defaults to 2 since most claim pages are wrapped by `withUser(withClaim(Page))`.
 * @param {object} [options.props] - Additional props to set on the PageComponent
 * @param {"mount"|"shallow"} [options.render] - Enzyme render method. Shallow renders by default.
 * @param {object} [options.userAttrs] - Additional attributes to set on the User
 * @param {boolean} [options.hasLoadedClaimDocuments] - Additional attributes to indicate document loading is finished
 * @param {boolean} [options.hasUploadedCertificationDocuments] - Additional attributes to set certification documents
 * @param {boolean} [options.hasUploadedIdDocuments] - Additional attributes to set id documents
 * @param {boolean} [options.hasLoadingDocumentsError] - Additional attributs to set errors for loading documents
 * @param {boolean} [options.hasLegalNotices] - Create legal notices for claim
 * @param {object} [options.warningsLists] - Mock appLogic.claims.warningsLists
 * @returns {{ appLogic: object, claim: Claim, wrapper: object }}
 */
const renderWithAppLogic = (PageComponent, options = {}) => {
  let appLogic, wrapper;
  options = merge(
    {
      claimAttrs: {},
      diveLevels: 2,
      employerClaimAttrs: {},
      props: {},

      // whether to use shallow() or mount()
      render: "shallow",
      userAttrs: {},
      warningsLists: {},
    },
    options
  );
  // Add claim and user instances to appLogic
  testHook(() => {
    appLogic = useAppLogic();
  });
  const claim = new Claim({
    application_id: "mock_application_id",
    ...options.claimAttrs,
  });
  appLogic.claims.claims = new ClaimCollection([claim]);
  appLogic.claims.hasLoadedClaimAndWarnings = jest
    .fn()
    .mockReturnValue(options.hasLoadedClaimAndWarnings || true);
  appLogic.claims.warningsLists = options.warningsLists;
  appLogic.employers.claim = new EmployerClaim(options.employerClaimAttrs);
  appLogic.auth.isLoggedIn = true;
  appLogic.users.requireUserConsentToDataAgreement = jest.fn();
  appLogic.users.user = new User({
    consented_to_data_sharing: true,
    user_id: "mock_user_id",
    ...options.userAttrs,
  });

  if (options.hasLoadedClaimDocuments) {
    appLogic.documents.hasLoadedClaimDocuments = jest
      .fn()
      .mockImplementation(() => true);
  }

  if (options.hasUploadedIdDocuments) {
    appLogic.documents.documents = appLogic.documents.documents.addItem(
      new Document({
        application_id: "mock_application_id",
        fineos_document_id: 1,
        document_type: DocumentType.identityVerification,
      })
    );
  }

  if (options.hasUploadedCertificationDocuments) {
    appLogic.documents.documents = appLogic.documents.documents.addItem(
      new Document({
        application_id: "mock_application_id",
        fineos_document_id: 2,
        document_type: DocumentType.medicalCertification,
      })
    );
  }

  if (options.hasLoadingDocumentsError) {
    appLogic.appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        meta: { application_id: "mock_application_id" },
        name: "DocumentsLoadError",
      }),
    ]);
  }

  if (options.hasLegalNotices) {
    appLogic.documents.documents = appLogic.documents.documents.addItem(
      new Document({
        application_id: "mock_application_id",
        created_at: "2021-01-01",
        document_type: DocumentType.approvalNotice,
        fineos_document_id: 3,
      })
    );
  }

  // Render the withClaim-wrapped page
  const component = (
    <PageComponent
      appLogic={appLogic}
      query={{ claim_id: claim.application_id }}
      {...options.props}
    />
  );

  act(() => {
    // Go two levels deep to get the component that was wrapped by withUser and withClaim
    if (options.render === "shallow") {
      wrapper = shallow(component);
      times(options.diveLevels, () => {
        wrapper = wrapper.dive();
      });
    } else {
      wrapper = mount(component);
      times(options.diveLevels, () => {
        wrapper = wrapper.childAt(0);
      });
    }
  });

  return { appLogic, claim, wrapper };
};

export default renderWithAppLogic;
