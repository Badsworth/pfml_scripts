import { Fineos } from "../submission/fineos.pages";
import { chooseRolePreset } from "../util/fineosRoleSwitching";

(() => {
  Fineos.withBrowser(
    async (page) => {
      await chooseRolePreset(
        page,
        "SRV_SSO_Account2@mass.gov",
        "DFML Appeals Administrator(sec)"
      );
    },
    { debug: true }
  );
})();
