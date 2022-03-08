import ApplicationImportsApi from "../api/ApplicationImportsApi";
import { ErrorsLogic } from "./useErrorsLogic";
import { PortalFlow } from "./usePortalFlow";

const useApplicationImportsLogic = ({
  errorsLogic,
  portalFlow,
}: {
  errorsLogic: ErrorsLogic;
  portalFlow: PortalFlow;
}) => {
  const importsApi = new ApplicationImportsApi();

  /**
   * Associate a claim created through the contact center with this user.
   * `import` is a reserved variable name in JS, so...using `associate` here.
   */
  const associate = async (formState: {
    absence_case_id: string | null;
    tax_identifier: string | null;
  }) => {
    errorsLogic.clearErrors();

    try {
      // Transform user input to conform to expected formatting for API
      const postData = { ...formState };
      postData.absence_case_id = postData.absence_case_id
        ? postData.absence_case_id.toUpperCase().trim()
        : null;

      const application = await importsApi.importClaim(postData);

      portalFlow.goToNextPage(
        {},
        {
          applicationAssociated: application.fineos_absence_id,
        }
      );
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  return {
    associate,
  };
};

export default useApplicationImportsLogic;
