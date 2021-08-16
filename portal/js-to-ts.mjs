import path from "path";
import { tsIgnorePlugin } from "ts-migrate-plugins";
import { migrate, MigrateConfig } from "ts-migrate-server";

// get input files folder
const inputDir = path.resolve(".");

// create new migration config and add ts-ignore plugin with empty options
const config = new MigrateConfig().addPlugin(tsIgnorePlugin, {});

// run migration
const exitCode = await migrate({ rootDir: inputDir, config });

process.exit(exitCode);
