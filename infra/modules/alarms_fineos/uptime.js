const assert = require('assert');
const options = {
    auth: {
        username: "" + $secure.FINEOS_BASIC_AUTH_USERNAME,
        password: "" + $secure.FINEOS_BASIC_AUTH_PASSWORD,
        sendImmediately: true,
    },
    // Enable cookie jar, which is necessary for storing session cookies.
    jar: true,
};

$util.insights.set("environment", config.environment);
$http.get(config.fineos_url, options, (err, response, body) => {
    assert.equal(response.statusCode, 200);
    const parts = /<span>Version: (.+?)<\/span>/.exec(body);
    assert(parts, "Version string was found");
    console.log(`Current Fineos version is ${parts[1]}`);
    $util.insights.set("fineos_version", parts[1]);
});
