// Note: At compile time, a `config` object is added above this line by Terraform.
const assert = require('assert');
const options = {
    auth: {
        // This strange syntax is necessary to cast the secrets to a string
        // for use later. Otherwise, it's of type Secret, and the script does
        // not pass validation.
        username: "" + $secure.FINEOS_BASIC_AUTH_USERNAME,
        password: "" + $secure.FINEOS_BASIC_AUTH_PASSWORD,
        sendImmediately: true,
    },
    // Enable cookie jar, which is necessary for storing session cookies.
    jar: true,
};

// These attributes are set on the `SyntheticCheck` event.
// They can be queried on later on under the `custom` namespace. Eg:
// `custom.environment`, or `custom.fineos_version`.
$util.insights.set("environment", config.environment);
$http.get(config.fineos_url, options, (err, response, body) => {
    assert.equal(response.statusCode, 200);
    const parts = /<span>Version: (.+?)<\/span>/.exec(body);
    assert(parts, "Version string was found");
    console.log(`Current Fineos version is ${parts[1]}`);
    $util.insights.set("fineos_version", parts[1]);
});
