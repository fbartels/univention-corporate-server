# -*- coding: utf-8 -*-
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
import sys
from univention.listener.exceptions import ListenerModuleConfigurationError
try:
	from typing import Any, Callable, Dict, List, Tuple
	from univention.listener.handler_configuration import ListenerModuleConfiguration
	from univention.listener.handler import ListenerModuleHandler
except ImportError:
	pass


class ListenerModuleAdapter(object):
	"""
	Adapter to convert the univention.listener.listener_module interface to
	the existing listener module interface.

	Use in a classic listener module like this:
	globals().update(ListenerModuleAdapter(MyListenerModuleConfiguration()).get_globals())
	"""
	_support_async = False

	def __init__(self, module_configuration, *args, **kwargs):
		# type: (ListenerModuleConfiguration, *Tuple, **Dict) -> None
		"""
		:param module_configuration: ListenerModuleConfiguration object
		"""
		self.config = module_configuration  # type: ListenerModuleConfiguration
		if (self.config.get_run_asynchronously() or self.config.get_parallelism() > 1) and not self._support_async:
			raise ListenerModuleConfigurationError(
				'Loading of asynchronous listener modules must be done with an AsyncListenerModuleAdapter.'
			)
		if self.config.get_parallelism() > 1 and not self.config.get_run_asynchronously():
			self.config.logger.warn(
				'Configuration of "parallelism > 1" implies "run_asynchronously = True". To prevent this warning '
				'configure it in your ListenerModuleConfiguration class.'
			)
			self.config.run_asynchronously = True
		self._ldap_cred = dict()  # type: Dict[str, str]
		self.__module_handler = None  # type: ListenerModuleHandler
		self._saved_old = dict()  # type: Dict[str, List[str]]
		self._saved_old_dn = None  # type: str
		self._rename = False  # type: bool
		self._renamed = False  # type: bool

	def get_globals(self):  # type: () -> Dict[str, Any]
		"""
		Returns the variables to be written to the module namespace, that
		make up the legacy listener module interface.

		:return: dict(name, description, filter_s, attributes, modrdn,
		handler, initialize, clean, prerun, postrun, setdata, ..)
		"""
		name = self.config.get_name()
		description = self.config.get_description()
		filter_s = self.config.get_ldap_filter() if self.config.get_active() else '(listenerModule=deactivated)'
		attributes = self.config.get_attributes()
		modrdn = 1
		handler = self._handler
		initialize = self._lazy_initialize
		clean = self._lazy_clean
		prerun = self._lazy_pre_run
		postrun = self._lazy_post_run
		setdata = self._setdata
		return dict(
			name=name,
			description=description,
			filter=filter_s,
			attributes=attributes,
			modrdn=modrdn,
			handler=handler,
			initialize=initialize,
			clean=clean,
			prerun=prerun,
			postrun=postrun,
			setdata=setdata
		)

	def _setdata(self, key, value):  # type: (str, str) -> None
		self._ldap_cred[key] = value
		if all(a in self._ldap_cred for a in ('basedn', 'basedn', 'bindpw', 'ldapserver')):
			self.config.set_ldap_credentials(
				self._ldap_cred['basedn'],
				self._ldap_cred['binddn'],
				self._ldap_cred['bindpw'],
				self._ldap_cred['ldapserver']
			)

	@property
	def _module_handler(self):  # type: () -> ListenerModuleHandler
		if not self.__module_handler:
			self.__module_handler = self.config.get_listener_module_instance()
		return self.__module_handler

	def _handler(self, dn, new, old, command):  # type: (str, Dict[str, List[str]], Dict[str, List[str]], str) -> None
		if command == 'r':
			self._saved_old = old
			self._saved_old_dn = dn
			self._rename = True
			self._renamed = False
			return
		elif command == 'a' and self._rename:
			old = self._saved_old

		try:
			if old and not new:
				self._module_handler.remove(dn, old)
			elif old and new:
				if self._renamed and not self._module_handler.diff(old, new):
					# ignore second modify call after a move if no non-metadata
					# attribute changed
					self._rename = self._renamed = False
					return
				self._module_handler.modify(dn, old, new, self._saved_old_dn if self._rename else None)
				self._renamed = self._rename
				self._rename = False
				self._saved_old_dn = None
			elif not old and new:
				self._module_handler.create(dn, new)
		except Exception:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			self._module_handler.error_handler(dn, old, new, command, exc_type, exc_value, exc_traceback)

	def _lazy_initialize(self):  # type: () -> Callable[None]
		return self._module_handler.initialize()

	def _lazy_clean(self):  # type: () -> Callable[None]
		return self._module_handler.clean()

	def _lazy_pre_run(self):  # type: () -> Callable[None]
		return self._module_handler.pre_run()

	def _lazy_post_run(self):  # type: () -> Callable[None]
		return self._module_handler.post_run()