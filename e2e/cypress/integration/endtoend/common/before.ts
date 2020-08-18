import { Before } from "cypress-cucumber-preprocessor/steps";
import { setFeatureFlags, catchStatusError } from "@/index";

Before({ tags: "@setFeatureFlags" }, () => setFeatureFlags());
Before({ tags: "@catchStatusError" }, () => catchStatusError());
