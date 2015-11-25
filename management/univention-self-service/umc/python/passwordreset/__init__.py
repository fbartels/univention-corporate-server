#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: password reset service
#
# Copyright 2015 Univention GmbH
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
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import traceback
import datetime
import random
import string
import atexit
from functools import wraps
from ldap import LDAPError
from ldap.filter import escape_filter_chars
import pylibmc

from univention.lib.i18n import Translation
from univention.uldap import getMachineConnection
import univention.admin.uldap
import univention.admin.uexceptions
import univention.admin.config
import univention.admin.objects
import univention.admin.uexceptions as udm_errors
from univention.management.console.base import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer
from univention.management.console.modules import UMC_Error
from univention.management.console.ldap import get_user_connection

from univention.management.console.modules.passwordreset.tokendb import TokenDB, MultipleTokensInDB
from univention.management.console.modules.passwordreset.sending import get_plugins as get_sending_plugins

_ = Translation('univention-self-service-passwordreset-umc').translate

TOKEN_VALIDITY_TIME = 3600
MEMCACHED_SOCKET = "/var/run/memcached-univention-self-service.socket"


def prevent_denial_of_service(func):
	@wraps(func)
	def _decorated(self, *args, **kwargs):
		def _check_limits(limits):
			limit_reached = False
			for key, decay, limit in limits:
				# Not really a "decay", as for that we'd have to store the date for
				# each request. Then a moving window could be implemented. But
				# my guess is that we won't need that, so this is simpler.
				# Continue even if a limit was reached, so that all counters are
				# incremented.
				try:
					count = self.memcache.incr(key)
				except pylibmc.NotFound:
					count = 1
					self.memcache.set(key, count, decay)
				if count > limit:
					limit_reached = True
			return limit_reached

		# check total request limits
		total_limit_reached = _check_limits(self.total_limits)

		# check user request limits
		try:
			if "username" in kwargs:
				username = kwargs["username"]
			else:
				username = args[0].options.get("username")
		except (IndexError, AttributeError, KeyError, TypeError) as e:
			# args[0] is not the expected 'request'
			MODULE.error("prevent_denial_of_service() could not find username argument. self: %r args: %r kwargs: %r exception: %s" % (self, args, kwargs, traceback.format_exc()))
			raise

		user_limits = [
			("{}_min".format(username), 60, self.limit_user_min),
			("{}_hour".format(username), 3600, self.limit_user_hour),
			("{}_day".format(username), 86400, self.limit_user_day)
		]

		user_limit_reached = _check_limits(user_limits)

		if total_limit_reached or user_limit_reached:
			raise ConnectionLimitError(_("The allowed maximum number of connections to the server has been reached. Please retry later."))

		return func(self, *args, **kwargs)
	return _decorated


class UnknownMethodError(UMC_Error):
	status = 500


class MethodDisabledError(UMC_Error):
	status = 500


class ConnectionLimitError(UMC_Error):
	status = 503


class UnknownUserError(UMC_Error):
	pass


class Instance(Base):

	def init(self):
		if not ucr.is_true("umc/self-service/passwordreset/enabled"):
			err = "Module is disabled by UCR."
			MODULE.error(err)
			raise UMC_Error(err, status=500)

		self.usersmod = None
		self.usersmod_rw = None
		self.groupmod = None
		self.config = None
		self.lo = None
		self.lo_rw = None
		self.position = None
		self.position_rw = None

		self.db = TokenDB(MODULE)
		self.conn = self.db.conn
		atexit.register(self.db.close_db)
		if not self.db.table_exists():
			self.db.create_table()

		self.token_validity_period = ucr.get("umc/self-service/passwordreset/token_validity_period", 3600)
		try:
			self.token_validity_period = int(self.token_validity_period)
		except ValueError as e:
			err = _("umc/self-service/passwordreset/token_validity_period must be a number: {}").format(e)
			MODULE.error(err)
			raise UMC_Error(err, status=500)

		self.send_plugins = get_sending_plugins(MODULE.info)

		self.memcache = pylibmc.Client([MEMCACHED_SOCKET], binary=True)

		def _memcached_stats():
			MODULE.info("memcached_stats: {}".format(self.memcache.get_stats()))
		atexit.register(_memcached_stats)

		limit_total_min = ucr.get("umc/self-service/passwordreset/limit/total/min", 0)
		limit_total_hour = ucr.get("umc/self-service/passwordreset/limit/total/hour", 0)
		limit_total_day = ucr.get("umc/self-service/passwordreset/limit/total/day", 0)
		self.limit_user_min = ucr.get("umc/self-service/passwordreset/limit/per_user/min", 0)
		self.limit_user_hour = ucr.get("umc/self-service/passwordreset/limit/per_user/hour", 0)
		self.limit_user_day = ucr.get("umc/self-service/passwordreset/limit/per_user/day", 0)
		try:
			limit_total_min = int(limit_total_min)
			limit_total_hour = int(limit_total_hour)
			limit_total_day = int(limit_total_day)
			self.limit_user_min = int(self.limit_user_min)
			self.limit_user_hour = int(self.limit_user_hour)
			self.limit_user_day = int(self.limit_user_day)
		except ValueError as e:
			err = _("umc/self-service/passwordreset/limit/.* must be a number: {}").format(e)
			MODULE.error(err)
			raise UMC_Error(err, status=500)

		self.total_limits = [
			("tc_min", 60, limit_total_min),
			("tc_hour", 3600, limit_total_hour),
			("tc_day", 86400, limit_total_day)
		]

	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True))
	def get_contact(self, request):
		"""
		Get users contact data.

		:param request: arguments are username and password
		:return: list of dicts with users contact data
		"""
		username = request.options.get("username")
		password = request.options.get("password")
		if not username:
			raise UMC_Error(_("Empty username supplied."))
		self.auth(username, password)
		if self.is_blacklisted(username):
			raise UMC_Error(_("Service is not available for this user."))
		user = self.get_udm_user(username=username)
		if not self.send_plugins:
			raise UMC_Error(_('No password reset method available for this user.'))
		self.finished(
			request.id,
			[{
				"id": p.send_method(),
				"label": p.send_method_label(),
				"value": user[p.udm_property]
			} for p in self.send_plugins.values() if user[p.udm_property]]
		)

	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		email=StringSanitizer(required=False),
		mobile=StringSanitizer(required=False))
	@simple_response
	def set_contact(self, username, password, email=None, mobile=None):
		MODULE.info("set_contact(): username: {} password: ***** email: {} mobile: {}".format(username, email, mobile))
		dn = self.auth(username, password)
		if self.is_blacklisted(username):
			raise UMC_Error(_("Service is not available for this user."))
		if self.set_contact_data(dn, email, mobile):
			raise UMC_Error(_("Successfully changed your contact data."), status=200)

	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		method=StringSanitizer(required=True))
	@simple_response
	def send_token(self, username, method):
		MODULE.info("send_token(): username: '{}' method: '{}'.".format(username, method))
		try:
			blacklisted = self.is_blacklisted(username)
		except UnknownUserError:
			raise UMC_Error(_("No contact information to send a token for password recovery to has been found."))
		if blacklisted:
			raise UMC_Error(_("Service is not available for this user."))
		try:
			plugin = self.send_plugins[method]
		except KeyError:
			MODULE.error("send_token() method '{}' not in {}.".format(method, self.send_plugins.keys()))
			raise UMC_Error(_("Unknown recovery method '{}'.").format(method))
		# check if the user has the required attribute set
		user = self.get_udm_user(username=username)

		if len(user[plugin.udm_property]) > 0:
			# found contact info
			try:
				token_from_db = self.db.get_one(username=username)
			except MultipleTokensInDB as e:
				# this should not happen, delete all tokens
				MODULE.error("send_token(): {}".format(e))
				self.db.delete_tokens(username=username)
				token_from_db = None

			token = self.create_token(plugin.token_length)
			if token_from_db:
				# replace with fresh token
				MODULE.info("send_token(): Updating token for user '{}'...".format(username))
				self.db.update_token(username, method, token)
			else:
				# store a new token
				MODULE.info("send_token(): Adding new token for user '{}'...".format(username))
				self.db.insert_token(username, method, token)
			try:
				self.send_message(username, method, user[plugin.udm_property], token)
			except:
				MODULE.error("send_token(): Error sending token with via '{method}' to '{username}'.".format(
					method=method, username=username))
				self.db.delete_tokens(username=username)
				raise
			raise UMC_Error(_("Successfully send token.").format(method), status=200)
		else:
			# no contact info
			raise UMC_Error(_("No contact information to send a token for password recovery to has been found."))

	@prevent_denial_of_service
	@sanitize(
		token=StringSanitizer(required=True),
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True))
	@simple_response
	def set_password(self, token, username, password):
		MODULE.info("set_password(): username: '{}'.".format(username))
		try:
			token_from_db = self.db.get_one(token=token, username=username)
		except MultipleTokensInDB as e:
				# this should not happen, delete all tokens, raise Exception
				# regardless of correctness of token
				MODULE.error("set_password(): {}".format(e))
				self.db.delete_tokens(token=token, username=username)
				raise UMC_Error(_("A problem occurred on the server and has been corrected, please retry."), status=500)
		if token_from_db:
			if (datetime.datetime.now() - token_from_db["timestamp"]).seconds < TOKEN_VALIDITY_TIME:
				# token is correct and valid
				MODULE.info("Receive valid token for '{}'.".format(username))
				if self.is_blacklisted(username):
					# this should not happen
					MODULE.error("Found token in DB for blacklisted user '{}'.".format(username))
					self.db.delete_tokens(token=token, username=username)
					raise UMC_Error(_("Service is not available for this user."))
				ret = self.udm_set_password(username, password)
				self.db.delete_tokens(token=token, username=username)
				if ret:
					raise UMC_Error(_("Successfully changed your password."), status=200)
			else:
				# token is correct but expired
				MODULE.info("Receive correct but expired token for '{}'.".format(username))
				self.db.delete_tokens(token=token, username=username)
				raise UMC_Error(_("The token you supplied has expired. Please request a new one."))
		else:
			# no token in DB
			MODULE.info("Token not found in DB for user '{}'.".format(username))
			raise UMC_Error(_("The token you supplied could not be found. Please request a new one."))

	@prevent_denial_of_service
	@sanitize(username=StringSanitizer(required=True))
	def get_reset_methods(self, request):
		username = request.options.get("username")
		if not username:
			raise UMC_Error(_("Empty username supplied."))
		try:
			blacklisted = self.is_blacklisted(username)
		except UnknownUserError:
			raise UMC_Error(_('No password reset method available for this user.'))
		if blacklisted:
			raise UMC_Error(_("Service is not available for this user."))
		user = self.get_udm_user(username=username)
		if not self.send_plugins:
			raise UMC_Error(_('No password reset method available for this user.'))
		# return list of method names, for all LDAP attribs user has data
		reset_methods = [{"id": p.send_method(), "label": p.send_method_label()} for p in self.send_plugins.values() if user[p.udm_property]]
		if reset_methods:
			self.finished(request.id, reset_methods)
		else:
			raise UMC_Error(_('No password reset method available for this user.'))

	@staticmethod
	def create_token(length):
		# remove easily confusable characters
		chars = string.ascii_letters.replace("l", "").replace("I", "").replace("O", "") + "".join(map(str, range(2,10)))
		rand = random.SystemRandom()
		res = ""
		for _ in xrange(length):
			res += rand.choice(chars)
		return res

	def send_message(self, username, method, address, token):
		MODULE.info("send_message(): username: {} method: {} address: {}".format(username, method, address))
		try:
			plugin = self.send_plugins[method]
		except KeyError:
			raise UnknownMethodError("send_message(): Unknown method '{}'.".format(method))
		if not plugin.is_enabled:
			raise MethodDisabledError("send_message(): Method '{}' is disabled by UCR.".format(method))
		data = {
			"username": username,
			"address": address,
			"token": token}
		plugin.set_data(data)
		MODULE.info("send_message(): Running plugin of class {}...".format(plugin.__class__.__name__))
		try:
			plugin.send()
		except Exception as ex:
			raise UMC_Error(_("Error sending token: {}").format(ex), status=500)
		return True

	@staticmethod
	def auth(username, password):
		lo = None
		try:
			lo = getMachineConnection()
			binddn = lo.search(filter="(uid={})".format(escape_filter_chars(username)))[0][0]
			get_user_connection(binddn=binddn, bindpw=password)
		except (univention.admin.uexceptions.authFail, IndexError):
			raise UMC_Error(_("Username or password is incorrect."))
		except (LDAPError, udm_errors.ldapError, udm_errors.base):
			MODULE.error("auth(): ERROR: connecting to LDAP: {}".format(traceback.format_exc()))
			raise UMC_Error(_("Could not connect to the LDAP server."))
		finally:
			lo.lo.unbind()
		return binddn

	def set_contact_data(self, dn, email, mobile):
		try:
			user = self.get_udm_user(userdn=dn, admin=True)
			if email is not None and email.lower() != user["PasswordRecoveryEmail"].lower():
				user["PasswordRecoveryEmail"] = email
			if mobile is not None and mobile.lower() != user["PasswordRecoveryMobile"].lower():
				user["PasswordRecoveryMobile"] = mobile
			user.modify()
			return True
		except Exception, e:
			MODULE.error("set_contact_data(): {}".format(traceback.format_exc()))
			raise

	def udm_set_password(self, username, password):
		try:
			user = self.get_udm_user(username=username, admin=True)
			user["password"] = password
			user["pwdChangeNextLogin"] = 0
			user.modify()
			return True
		except udm_errors.pwToShort as ex:
			raise UMC_Error(str(ex))
		except udm_errors.pwalreadyused:
			raise UMC_Error(_("The Password has been used already. Please supply a new one."))
		except:
			MODULE.info("udm_set_password(): failed to set password: {}".format(traceback.format_exc()))
			raise

	#TODO: decoratorize
	def is_blacklisted(self, username):
		def listize(li):
			return [x.lower() for x in map(str.strip, li.split(",")) if x]

		bl_users = listize(ucr.get("umc/self-service/passwordreset/blacklist/users", ""))
		bl_groups = listize(ucr.get("umc/self-service/passwordreset/blacklist/groups", ""))
		wh_users = listize(ucr.get("umc/self-service/passwordreset/whitelist/users", ""))
		wh_groups = listize(ucr.get("umc/self-service/passwordreset/whitelist/groups", ""))

		# user blacklist
		if username.lower() in bl_users:
			MODULE.info("is_blacklisted({}): match in blacklisted users".format(username))
			return True

		# get groups
		lo = getMachineConnection()
		try:
			userdn = lo.search(filter="(uid={})".format(escape_filter_chars(username)))[0][0]
			groups_dns = self.get_groups(userdn)
			for group_dn in list(groups_dns):
				groups_dns.extend(self.get_nested_groups(group_dn))
			groups_dns = list(set(groups_dns))
			gr_names = map(str.lower, self.dns_to_groupname(groups_dns))
		except IndexError:
			# no user or no group found
			raise UnknownUserError(_("Unknown user."))

		# group blacklist
		if any([gr in bl_groups for gr in gr_names]):
			MODULE.info("is_blacklisted({}): match in blacklisted groups".format(username))
			return True

		# if not on blacklist, check whitelists
		# user whitelist
		if username.lower() in wh_users:
			MODULE.info("is_blacklisted({}): match in whitelisted users".format(username))
			return False

		# group whitelist
		if any([gr in wh_groups for gr in gr_names]):
			MODULE.info("is_blacklisted({}): match in whitelisted groups".format(username))
			return False

		# not on either black or white list -> not allowed if whitelist exists, else OK
		MODULE.info("is_blacklisted({}): neither black nor white listed".format(username))
		return not (wh_users or wh_groups)

	def get_groups(self, userdn):
		user = self.get_udm_user(userdn=userdn)
		groups = user["groups"]
		prim_group = user["primaryGroup"]
		if prim_group not in groups:
			groups.append(prim_group)
		return groups

	def get_nested_groups(self, groupdn):
		group = self.get_udm_group(groupdn)
		res = group["nestedGroup"] or []
		for ng in list(res):
			res.extend(self.get_nested_groups(ng))
		return res

	def dns_to_groupname(self, dns):
		names = list()
		for groupdn in dns:
			group = self.get_udm_group(groupdn)
			names.append(group["name"])
		return names

	def get_udm_user(self, userdn=None, username=None, admin=False):
		if userdn:
			dn_part = userdn.partition(",")
			uidf = dn_part[0]
			base = dn_part[-1]
		elif username:
			uidf = 'uid={}'.format(escape_filter_chars(username))
			base = ""
		else:
			MODULE.error("userdn=None and username=None")
			raise UMC_Error(_("Program error. Please report this to the administrator."), status=500)

		if admin:
			if not self.usersmod_rw:
				if not self.config:
					self.config = univention.admin.config.config()
				univention.admin.modules.update()
				self.usersmod_rw = univention.admin.modules.get("users/user")
				if not self.lo_rw:
					self.lo_rw, self.position_rw = univention.admin.uldap.getAdminConnection()
				univention.admin.modules.init(self.lo_rw, self.position_rw, self.usersmod_rw)
			lo = self.lo_rw
			usersmod = self.usersmod_rw
		else:
			if not self.usersmod:
				if not self.config:
					self.config = univention.admin.config.config()
				univention.admin.modules.update()
				self.usersmod = univention.admin.modules.get("users/user")
				if not self.lo or not self.position:
					self.lo, self.position = univention.admin.uldap.getMachineConnection()
				univention.admin.modules.init(self.lo, self.position, self.usersmod)
			lo = self.lo
			usersmod = self.usersmod

		user = usersmod.lookup(self.config, lo, filter_s=uidf, base=base)[0]
		user.open()
		return user

	def get_udm_group(self, groupdn):
		dn_part = groupdn.partition(",")
		gidf = dn_part[0]
		base = dn_part[-1]

		if not self.groupmod:
			if not self.config:
				self.config = univention.admin.config.config()
			univention.admin.modules.update()
			self.groupmod = univention.admin.modules.get("groups/group")
			if not self.lo or not self.position:
				self.lo, self.position = univention.admin.uldap.getMachineConnection()
			univention.admin.modules.init(self.lo, self.position, self.groupmod)

		group = self.groupmod.lookup(self.config, self.lo, filter_s=gidf, base=base)[0]
		group.open()
		return group
