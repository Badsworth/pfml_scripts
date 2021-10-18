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

export function labelComponent(name) {
  switch (name) {
    case "api":
      return "API";
    default:
      return name[0].toUpperCase() + name.substring(1);
  }
}
