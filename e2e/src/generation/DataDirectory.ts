import path from "path";
import fs from "fs";
import { format as formatDate } from "date-fns";

export interface DataDirectory {
  dir: string;
  documents: string;
  employers: string;
  employees: string;
  claims: string;
  state: string;
  usedEmployees: string;
  prepare(): Promise<void>;
  join(...parts: string[]): string;
  dorFile(prefix: string): string;
}

export default function directory(
  name: string,
  rootDir?: string
): DataDirectory {
  const base = rootDir ?? path.join(__dirname, "..", "..", "data");
  const dir = path.join(base, name);
  const documents = path.join(dir, "documents");
  return {
    dir: dir,
    documents: documents,
    employers: path.join(dir, "employers.json"),
    employees: path.join(dir, "employees.json"),
    usedEmployees: path.join(dir, "used_employees.json"),
    claims: path.join(dir, "claims.ndjson"),
    state: path.join(dir, "state.json"),
    async prepare(): Promise<void> {
      await fs.promises.mkdir(documents, { recursive: true });
    },
    join(...parts: string[]): string {
      return path.join(dir, ...parts);
    },
    dorFile(prefix: string): string {
      const filename = `${prefix}_${formatDate(new Date(), "yyyyMMddHHmmss")}`;
      return path.join(dir, filename);
    },
  };
}
