/*
 * Copyright 2016-2017 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/dom-construct",
	"portal"
], function(lang, array, win, domConstruct, portal) {
	function log(description) {
		domConstruct.create('div', {
			innerHTML: description
		}, win.body());
	}

	var _successfulAssertions = 0;
	var _failedAssertiongs = 0;

	function assertEquals(x, y, description) {
		description = description || '';
		if (x != y) { 
			log(lang.replace('FAILURE: {0} and {1} are not equal! {2}', [x, y, description]));
			_failedAssertiongs += 1; 
		} else {
			_successfulAssertions += 1;
		}
	}

	function summary() {
		log(lang.replace('<br/> {0} successful and {1} failed tests.', [_successfulAssertions, _failedAssertiongs]));
		if (_failedAssertiongs === 0) {
			log('The tests look great :-) !');
		} else {
			log('Oh, still some work to do :-/ !');
		}
	}
	
	function testCanonicalizedIPAddresses() {
		log('<b>Testing canonicalize IP addresses...</b>');
		var _ipAddresses = [
			['1111:2222:3333:4444:5555:6666::', '1111:2222:3333:4444:5555:6666:0000:0000'],
			['1::6:77', '0001:0000:0000:0000:0000:0000:0006:0077'],
			['::11.22.33.44', '0000:0000:0000:0000:0000:0000:0b16:212c'],
			['a0a:0b0::11.22.33.44', '0a0a:00b0:0000:0000:0000:0000:0b16:212c'],
			['1.2.3.4', '0102:0304'],
			['a1a2:b1b2:0b3::', 'a1a2:b1b2:00b3:0000:0000:0000:0000:0000'],
			['2001:0DB8:0:CD30::', '2001:0DB8:0000:CD30:0000:0000:0000:0000']
		]

		array.forEach(_ipAddresses, function(i) {
			assertEquals(portal.canonicalizeIPAddress(i[0]), i[1]);
		});
	}

	function testLinkRanking() {
		log('<b>Testing link ranking...</b>');
		var _links = [[
			// description
			'Simple test with one relative link.',
			// <browserAddress>, [<possibleLink1>, ...], <bestLink>
			'http://www.example.com', ['/test'], '/test'
		], [
			'Relative links should always be preferred.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], 'https://foo.bar.com/test'
		], [
			'Relative links should always be preferred.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test', '/foobar/'], '/foobar/'
		], [
			'If browser address uses an FQDN, the FQDN address should always be taken.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], 'https://foo.bar.com/test'
		], [
			'If browser address uses an FQDN and no FQDN link is given, IPv4 should be preferred.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test'], '//192.168.10.10/test'
		], [
			'Relative links should always be preferred.',
			'http://192.168.10.33', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test', '/foobar/'], '/foobar/'
		], [
			'If browser address is IPv4, the IPv4 link should always be chosen.',
			'http://192.168.10.33', ['//192.177.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//192.177.10.10/test'
		], [
			'Amoung various IPv4 addresses, the best address match should be taken.',
			'http://192.168.10.33', ['https://192.177.10.10/test', '//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//192.168.10.10/test'
		], [
			'Relative links should always be preferred.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test', '/foobar/'], '/foobar/'
		], [
			'If browser address is IPv6, the IPv6 link should be chosen.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//[1111::2222]/test'
		], [
			'Among various IPv6 addresses, the best address match should be chosen.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://[3333::2211:1122]/test', 'https://foo.bar.com/test'], 'https://[3333::2211:1122]/test'
		], [
			'A protocol relative link should always be preferred.',
			'http://www.example.com', ['//foo.bar.com/relative', 'http://foo.bar.com/http', 'https://foo.bar.com/https'], '//foo.bar.com/relative'
		], [
			'The link that matches the current protocol should be preferred.',
			'http://www.example.com', ['http://foo.bar.com/http', 'https://foo.bar.com/https'], 'http://foo.bar.com/http'
		], [
			'The link that matches the current protocol should be preferred.',
			'https://www.example.com', ['http://foo.bar.com/http', 'https://foo.bar.com/https'], 'https://foo.bar.com/https'
		]];

		array.forEach(_links, function(i) {
			assertEquals(i[3], portal.getHighestRankedLink(i[1], i[2]), i[0]);
		});
	}

	function testConversionToRelativeLink() {
		log('<b>Testing conversion to relative link...</b>');
		var _links = [
			['master.mydomain.de', ['http://[1111:2222::]/test', '//192.168.3.2/test'], null],
			['master.mydomain.de', ['http://[1111:2222::]/test', '/test', '//192.168.3.2/test'], '/test'],
			['master.mydomain.de', ['//foo.bar.com/test', 'https://master.mydomain.de/test'], '/test'],
			['slave.mydomain.de', ['//foo.bar.com/test', 'http://master.mydomain.de/test'], null]
		];

		array.forEach(_links, function(i) {
			assertEquals(i[2], portal.getRelativeLink(i[0], i[1]));
		});
	}

	return {
		start: function() {
			testCanonicalizedIPAddresses();
			testLinkRanking();
			testConversionToRelativeLink();
			summary();
		}
	};
});