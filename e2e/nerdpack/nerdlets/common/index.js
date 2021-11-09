export const COMPONENTS = ["portal", "api", "fineos"];
export const COMPONENTS_WIDTH = { portal: "20%", api: "20%", fineos: "30%" };
export const ENVS = [
  "prod",
  "breakfix",
  "training",
  "uat",
  "performance",
  "stage",
  "cps-preview",
  "test",
];

export const extractGroup = (item, name) => {
  const group = item.metadata.groups.find((g) => g.name === name);
  if (group) {
    return group.value;
  }
  throw new Error(`Unable to determine ${name}`);
};

export const labelComponent = (name) => {
  switch (name) {
    case "api":
      return "API";
    default:
      return name[0].toUpperCase() + name.substring(1);
  }
};

export const labelEnv = (name) => {
  name = name.toLowerCase();
  switch (name) {
    case "test":
      return "Test/DT2";
    case "stage":
      return "Stage/IDT";
    case "cps-preview":
      return "CPS-Preview/DT3";
    case "breakfix":
      return "Breakfix/PFX";
    case "uat":
      return "UAT";
    default:
      return name[0].toUpperCase() + name.substring(1);
  }
};
