/*
 * Copyright 2015 Univention GmbH
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
/*global define require console window */

define([
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/io-query",
	"dojo/query",
	"dojo/on",
	"dojo/dom",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/request/xhr",
	"../ucs/text!/ucs-overview/welcome.json",
	"../ucs/i18n!welcome,ucs"
], function(lang, kernel, array, ioQuery, query, on, dom, domConstruct, domAttr, domStyle, domClass, domGeometry, xhr, data, _) {
	return {
		start: function() {
			this.replaceTitle();
			this.addApplianceLogo();
			this.insertLinks();
			this.showDesktop();
			this.listenLinks();
		},

		replaceTitle: function() {
			if (data['umc/web/appliance/name']) {
				var title = _('Welcome to {0} Univention App', [data['umc/web/appliance/name']]);
				var titleNode = query('h1', 'title')[0];
				domAttr.set(titleNode, 'data-i18n', title);
				titleNode.innerHTML = title;
				query('title')[0].innerHTML = title;
			}
		},

		addApplianceLogo: function() {
			if (data['umc/web/appliance/logo']) {
				var path = data['umc/web/appliance/logo'];
				if (path[0] !== '/') {
					path = '/univention-management-console/js/dijit/themes/umc/' + path;
				}
				domStyle.set('welcome-appliance-logo', 'backgroundImage', lang.replace('url("{0}")', [path]));
			}
		},

		insertLinks: function() {
			var alternatives = dom.byId('welcome-url-alternative');
			array.forEach(data['ip_addresses'].concat([data['hostname'] + '.' + data['domainname']]).concat(data['ip6_addresses']), function(address, i, arr) {
				address = this.formatUrl(address, data['ip6_addresses'].indexOf(address) !== -1);
				if (i == 0) {
					dom.byId('welcome-url').innerHTML = address;
				} else {
					domClass.toggle(alternatives, 'dijitHidden', false);
					domConstruct.create('a', {innerHTML: address}, alternatives);
				}
			}, this);
		
		},

		showDesktop: function() {
			domClass.toggle(dom.byId('welcome-desktop'), 'dijitHidden', getQuery('showDesktop') != 'true');
		},

		listenLinks: function() {
			on(dom.byId('welcome-desktop-link'), 'click', function() {
				domClass.toggle('welcome-desktop-text', 'dijitHidden', false);
			});
			on(dom.byId('welcome-command-link'), 'click', function() {
				domClass.toggle('welcome-command-text', 'dijitHidden', false);
			});
			var port = String(parseInt(getQuery('port')));
			on(dom.byId('switch-cli'), 'click', function() {
				console.log('switch-cli', arguments);
				xhr.get('http://localhost:' + port + '/switch-cli');
			});
			on(dom.byId('switch-desktop'), 'click', function() {
				console.log('switch-desktop', arguments);
				xhr.get('http://localhost:' + port + '/switch-desktop');
			});
		},

		formatUrl: function(url, ip6) {
			if (ip6) {
				url = '[' + url + ']';
			}
			return 'https://' + url + '/';
		}
	};
});