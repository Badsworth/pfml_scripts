import { Page } from "playwright-chromium";
import {
  ConfigPage,
  Fineos,
  FineosRoles,
  FineosSecurityGroups,
} from "../submission/fineos.pages";

const presets: Record<
  FineosSecurityGroups,
  {
    role: FineosRoles | FineosSecurityGroups;
    supervisorOf: boolean;
    memberOf: boolean;
  }[]
> = {
  // DFML Appeals
  "DFML Appeals Administrator(sec)": [
    { role: "DFML Appeals", supervisorOf: true, memberOf: true },
  ],
  "DFML Appeals Examiner I(sec)": [
    { role: "DFML Appeals", supervisorOf: true, memberOf: true },
  ],
  "DFML Appeals Examiner II(sec)": [
    { role: "DFML Appeals", supervisorOf: true, memberOf: true },
  ],
  // DFML Program Integrity
  "DFML Claims Examiners(sec)": [
    { role: "DFML Program Integrity", supervisorOf: true, memberOf: true },
  ],
  "DFML Claims Supervisors(sec)": [
    { role: "DFML Program Integrity", supervisorOf: true, memberOf: true },
  ],
  "DFML Compliance Analyst(sec)": [
    { role: "DFML Program Integrity", supervisorOf: true, memberOf: true },
  ],
  "DFML Compliance Supervisors(sec)": [
    { role: "DFML Program Integrity", supervisorOf: true, memberOf: true },
  ],
  // DFML IT
  "DFML IT(sec)": [{ role: "DFML IT", supervisorOf: true, memberOf: true }],
  // SaviLinx
  "SaviLinx Agents (sec)": [
    { role: "SaviLinx", supervisorOf: true, memberOf: true },
  ],
  "SaviLinx Secured Agents(sec)": [
    { role: "SaviLinx", supervisorOf: true, memberOf: true },
  ],
  "SaviLinx Supervisors(sec)": [
    { role: "SaviLinx", supervisorOf: true, memberOf: true },
  ],
  // Post-Prod Admin(sec) - the permission to change permissions
  "Post-Prod Admin(sec)": [],
};

async function chooseRolePreset(
  page: Page,
  userId: string,
  preset: FineosSecurityGroups
) {
  if (userId === "SRV_SSO_Account")
    throw new Error("Changing role permissions for this account is disallowed");
  const configPage = await ConfigPage.visit(page);
  await configPage.setRoles(userId, [
    { role: preset, memberOf: true, supervisorOf: false },
    ...presets[preset],
  ]);
}
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
