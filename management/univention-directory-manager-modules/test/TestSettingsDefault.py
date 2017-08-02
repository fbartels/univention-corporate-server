# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  unit tests: settings/default tests
#
# Copyright 2004-2017 Univention GmbH
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


from GenericTest import GenericTestCase


class SettingsDefaultTestCase(GenericTestCase):

	def __init__(self, *args, **kwargs):
		self.modname = 'settings/default'
		super(SettingsDefaultTestCase, self).__init__(*args, **kwargs)
		self.container = self.rdn('cn=default,cn=univention')
		self.defaults = {
			'defaultGroup':
			self.rdn('cn=Domain Users,cn=groups'),
			'defaultComputerGroup':
			self.rdn('cn=Windows Hosts,cn=groups'),
			'defaultDomainControllerGroup':
			self.rdn('cn=DC Slave Hosts,cn=groups'),
			'defaultKdeProfiles':
			{'append':
			 ['none',
			  '/usr/share/univention-kde-profiles/kde.lockeddown',
			  '/usr/share/univention-kde-profiles/kde.restricted'],
			 'remove':
			 ['moobaz', 'goobaz']},
		}

	def setUp(self):
		super(SettingsDefaultTestCase, self).setUp()
		self.modifyProperties = {
			'defaultGroup':
			self.rdn('cn=Domain Admins,cn=groups'),
			'defaultComputerGroup':
			self.rdn('cn=Domain Users,cn=groups'),
			'defaultDomainControllerGroup':
			self.rdn('cn=Domain Users,cn=groups'),
			'defaultKdeProfiles':
			{'append': ['moobaz', 'goobaz'],
			 'remove': []},
		}
		self.__success = False

	def runTest(self):
		self.dn = self.container
		self.name = 'default'
		self.testModify()
		self.modifyProperties = self.defaults
		self.testModify()
		self.__success = True

	def tearDown(self):
		super(SettingsDefaultTestCase, self).tearDown()
		if not self.__success:
			self.modify(self.defaults, self.dn)


def suite():

	import unittest
	suite = unittest.TestSuite()
	suite.addTest(SettingsDefaultTestCase())
	return suite


if __name__ == '__main__':
	import unittest
	unittest.TextTestRunner().run(suite())