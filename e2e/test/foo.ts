import { withGeneratedDocument } from "./util";

withGeneratedDocument("pdf", [5, "kb"], (path) => {
    console.log(path);
});
