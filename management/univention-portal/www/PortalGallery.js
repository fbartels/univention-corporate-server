/*
 * Copyright 2016-2018 Univention GmbH
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
/*global define, window, location*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/aspect",
	"dojo/query",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/dnd/Source",
	"put-selector/put",
	"umc/tools",
	"umc/widgets/AppGallery",
	"./tools"
], function(declare, lang, array, on, aspect, query, domClass, domConstruct, domGeometry, domStyle, Memory, Observable, Source, put, tools, AppGallery, portalTools) {
	var _regIPv6Brackets = /^\[.*\]$/;

	var find = function(list, testFunc) {
		var results = array.filter(list, testFunc);
		return results.length ? results[0] : null;
	};

	var getHost = function(/*Array*/ ips, /*string*/ fqdn) {
		var host = window.location.host;

		if (tools.isIPv6Address(host)) {
			var ipv6 = find(ips, tools.isIPv6Address);
			if (ipv6 && !_regIPv6Brackets.test(ipv6)) {
					return '[' + ipv6 + ']';
			}
			if (ipv6) {
				return ipv6;
			}
			// use IPv4 as fallback
			return find(ips, tools.isIPv4Address);
		}
		if (tools.isIPv4Address(host)) {
			return find(ips, tools.isIPv4Address);
		}
		return fqdn;
	};

	return declare("PortalGallery", [ AppGallery ], {
		iconClassPrefix: 'umcPortal',

		domainName: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.baseClass += ' umcPortalGallery';
			this._rowHandlers = [];
			this._dndExternalDropMap = {};
		},

		buildRendering: function() {
			this.inherited(arguments);
			if (!this.useDnd) {
				return;
			}

			var dndContainer = put(this.domNode, 'div');
			this.dndPlaceholderHideout = put(this.domNode, 'div.dndPlaceholderHideout');

			this.dndSource = new Source(dndContainer, {
				horizontal: true,
				copyState: function() {
					return false; // do not allow copying
				},
				creator: lang.hitch(this, function(item, hint) {
					var renderInfo = this.getRenderInfo(item);
					var node = this.getDomForRenderRow(renderInfo);
					this._resizeDndNode(node);

					if (hint === 'avatar') {
						return {node: put('div.umcAppGallery', node)};
					}

					return {
						node: put('div', node), // wrap the tile so that the margin is part of the node and there is is no gap between the tiles
						data: item
					};
				})
			});
			this.dndSource.store = new Memory({});
			this.dndSource.externalDropMap = {};
			var domString = '' +
				'<div class="dndPlaceholder dojoDndItem">' +
					'<div class="umcGalleryWrapperItem portalEditAddEntryDummy">' +
						'<div class="cornerPiece boxShadow bl">' +
							'<div class="hoverBackground"></div>' +
						'</div>' +
						'<div class="cornerPiece boxShadow tr">' +
							'<div class="hoverBackground"></div>' +
						'</div>' +
						'<div class="cornerPiece boxShadowCover bl"></div>' +
					'</div>' +
				'</div>';
			this.dndPlaceholder = domConstruct.toDom(domString);
			put(this.dndPlaceholderHideout, this.dndPlaceholder);

			aspect.around(this.dndSource, 'onDropExternal', lang.hitch(this, function(origFunction) {
				return lang.hitch(this, function(source, nodes, copy) {
					array.forEach(nodes, lang.hitch(this, function(inode) {
						var data = source.getItem(inode.id).data;
						delete source.externalDropMap[data.dn];
						if (!this.store.get(data.dn)) {
							this.dndSource.externalDropMap[data.dn] = this.category;
						}
						this.dndSource.store.add(data);
						source.store.remove(data.dn);
					}));
					origFunction.apply(this.dndSource, [source, nodes, copy]);
				});
			}));
			aspect.after(this.dndSource, '_addItemClass', lang.hitch(this, function(target, cssClass) {
				if (this.dndSource.isDragging) {
					if (target === this.dndPlaceholder) {
						return;
					}

					// if the placeholder tile is not placed yet, ...
					if (this.dndPlaceholderHideout.firstChild === this.dndPlaceholder) {
						// and we come from outside the dndSource,
						// place the placeholder in place of hovered tile
						if (!this.dndSource.current && this.dndSource.anchor /* check for anchor to see if we are in the same category as the dragged tile */) {
							var putCombinator = query(lang.replace('#{0} ~ #{1}', [this.dndSource.anchor.id, target.id]), this.dndSource.parent).length ? '+' : '-';
							put(target, putCombinator, this.dndPlaceholder);
						} else {
							// this case is when the drag event ist started.
							// Put the placeholder in the place of the dragged tile
							put(target, '-', this.dndPlaceholder);
						}
						return;
					}

					// if we hover over a different tile while dragging and while the placeholder tile is placed
					// we move the placeholder tile to the hovered tile
					if (cssClass === 'Over') {
						// if we hover a tile to the right of the placeholder we want to place the placeholder to the right of the hovered tile
						// and vice versa
						var putCombinator = query(lang.replace('#{0} ~ .dndPlaceholder', [target.id]), this.dndSource.parent).length ? '-' : '+';
						put(target, putCombinator, this.dndPlaceholder);
					}
				}
			}), true);
			aspect.before(this.dndSource, 'onDropInternal', lang.hitch(this, function() {
				if (!this.dndSource.current && this.dndSource.parent.lastChild === this.dndPlaceholder) {
					this.dndSource.current = this.dndPlaceholder.previousSibling;
				}
			}));
			aspect.after(this.dndSource, 'onDropInternal', lang.hitch(this, function() {
				put(this.dndPlaceholderHideout, this.dndPlaceholder);
			}));
			aspect.after(this.dndSource, 'onDndCancel', lang.hitch(this, function() {
				put(this.dndPlaceholderHideout, this.dndPlaceholder);
			}));
			aspect.after(this.dndSource, 'onDraggingOut', lang.hitch(this, function() {
				put(this.dndPlaceholderHideout, this.dndPlaceholder);
			}));
			aspect.after(this.dndSource, 'onMouseMove', lang.hitch(this, function() {
				if (!this.dndSource.isDragging) {
					return;
				}
				if (!this.dndSource.current && this.dndSource.parent.lastChild !== this.dndPlaceholder) {
					put(this.dndSource.parent, this.dndPlaceholder);
				}
			}));
		},

		insertDndData: function(data) {
			this.dndSource.store.setData(data);
			this.dndSource.insertNodes(false, this.dndSource.store.query());
		},

		postCreate: function() {
			// TODO: this changes with Dojo 2.0
			this.domNode.setAttribute("widgetId", this.id);

			// add specific DOM classes
			if (this.baseClass) {
				domClass.add(this.domNode, this.baseClass);
			}

			if (this.store) {
				this.set('store', this.store);
			}
		},

		startup: function() {
			// calling startup causes the entries to be rendered 3 times from
			// somewhere in the inheritence chain.
			// We actally do not need (want) any of the startup code from the
			// inheritance chain. It is just resizing which does not matter
			// with the portal tile design and issuing the first rendering of
			// the entries which is triggered by setting the store in
			// this.postCreate 
			return;
		},

		getRenderInfo: function(item) {
			return lang.mixin(this.inherited(arguments), {
				itemSubName: item.host_name
			});
		},

		getIconClass: function(logoUrl) {
			return portalTools.getIconClass(logoUrl);
		},

		getStatusIconClass: function() {
			return (this.editMode && !this.dndMode) ? 'editIcon' : 'noStatus';
		},

		renderRow: function(item) {
			if (item.portalEditAddEntryDummy) {
				var domString = '' +
					'<div class="umcGalleryWrapperItem portalEditAddEntryDummy">' +
						'<div class="cornerPiece boxShadow bl">' +
							'<div class="hoverBackground"></div>' +
						'</div>' +
						'<div class="cornerPiece boxShadow tr">' +
							'<div class="hoverBackground"></div>' +
						'</div>' +
						'<div class="cornerPiece boxShadowCover bl"></div>' +
						'<div class="dummyIcon"></div>' +
					'</div>';
				var domNode = domConstruct.toDom(domString);
				this._rowHandlers.push(on(domNode, 'click', lang.hitch(this, 'onAddEntry', this.category)));
				return domNode;
			}

			var domNode = this.inherited(arguments);
			if (this.editMode) {
				this._rowHandlers.push(on(domNode, 'click', lang.hitch(this, 'onEditEntry', this.category, item)));
			} else {
				put(domNode, 'a[href=$]', this._getWebInterfaceUrl(item), query('.umcGalleryItem', domNode)[0]);
			}
			return domNode;
		},

		editMode: null,
		_rowHandlers: null,
		renderArray: function() {
			array.forEach(this._rowHandlers, function(ihandler) {
				ihandler.remove();
			});
			this.inherited(arguments);
		},

		// can't be used with dojo/on since this widget does not inherit from _WidgetBase
		// use dojo/aspect.after
		onAddEntry: function() {
			// event stub
		},

		onEditEntry: function(item) {
			// event stub
		},

		_getProtocolAndPort: function(app) {
			var protocol = window.location.protocol;
			var port = null;

			if (protocol === 'http:') {
				port = app.web_interface_port_http;
				if (!port && app.web_interface_port_https) {
					protocol = 'https:';
					port = app.web_interface_port_https;
				}
			} else if (protocol === 'https:') {
				port = app.web_interface_port_https;
				if (!port && app.web_interface_port_http) {
					protocol = 'http:';
					port = app.web_interface_port_http;
				}
			}

			if (port && app.auto_mod_proxy) {
				if (protocol === 'http:') {
					port = '80';
				} else if (protocol === 'https:') {
					port = '443';
				}
			}

			if (port === '80') {
				protocol = 'http:';
				port = null;
			} else if (port === '443') {
				protocol = 'https:';
				port = null;
			}
			if (port) {
				port = ':' + port;
			} else {
				port = '';
			}

			return {
				protocol: protocol,
				port: port
			};
		},

		_getWebInterfaceUrl: function(app) {
			if (!app.web_interface) {
				return "";
			}
			if (app.web_interface.indexOf('/') !== 0) {
				return app.web_interface;
			}

			var protocolAndPort = this._getProtocolAndPort(app);
			var protocol = protocolAndPort.protocol;
			var port = protocolAndPort.port;

			var fqdn = app.host_name + '.' + this.domainName;
			var host = (app.host_ips) ? getHost(app.host_ips, fqdn) : window.location.host;

			var url = lang.replace('{protocol}//{host}{port}{webInterface}', {
				protocol: protocol,
				host: host,
				port: port,
				webInterface: app.web_interface
			});

			return url;
		},

		_resizeDndNode: function(node) {
			var wrapper = put('div.umcAppGallery.dijitOffScreen', node);
			put(dojo.body(), wrapper);
			var defaultValues = this._getDefaultValuesForResize('.umcGalleryName');
			var defaultHeight = defaultValues.height;
			var fontSize = parseInt(defaultValues.fontSize, 10) || 16;
			query('.umcGalleryNameContent', node).forEach(lang.hitch(this, function(inode) {
				var fontSize = parseInt(defaultValues.fontSize, 10) || 16;
				while (domGeometry.position(inode).h > defaultHeight) {
					fontSize--;
					domStyle.set(inode, 'font-size', fontSize + 'px');
				}
			}));
			dojo.body().removeChild(wrapper);
		}
	});
});
