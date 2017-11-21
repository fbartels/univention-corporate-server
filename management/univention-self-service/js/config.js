// get locale from query string
function getQuery(/*String*/ param, /*mixed*/ defaultVal) {
	// parse the URI query string
	var query = window.location.search.substring(1);
	var vars = query.split('&');
	for (var i = 0; i < vars.length; i++) {
		// parse the tuple
		var tuple = vars[i].split('=');
		// check whether we found the particular parameter we are interested in
		if (2 == tuple.length && param == tuple[0]) {
			return tuple[1];
		}
	}
}

locale = getQuery('lang');
if (locale) {
	locale = locale.replace('_', '-');
}

// load the javascript module that is specified in the hash
var selfService = document.location.hash.substr(1);

var dojoConfig = {
	isDebug: false,
	locale: locale,
	async: true,
	callback: function() {
		require([
			"dojo/hash",
			"dojo/topic",
			"ucs/" + selfService,
			"ucs/LanguagesDropDown",
			"dojo/domReady!"
		], function(hash, topic, app, LanguagesDropDown) {
			app.start();
			LanguagesDropDown.start();
			topic.subscribe("/dojo/hashchange", function(changedHash) {
				window.location.reload();
			});
		});
	}
};