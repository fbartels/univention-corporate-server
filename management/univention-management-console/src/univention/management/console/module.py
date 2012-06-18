# -*- coding: utf-8 -*-
#
# Univention Management Console
#  next generation of UMC modules
#
# Copyright 2011-2012 Univention GmbH
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

"""
Module definitions
==================

The UMC server does not load the python modules to get the details about
the modules name, description and functionality. Therefor each UMC
module must provide an XML file containing this kind of information.

The following example defines a module with the id *udm* ::

 <?xml version="1.0" encoding="UTF-8"?>
 <umc version="2.0">
   <module id="udm" icon="udm/module" version="1.0">
     <name>Univention Directory Manager</name>
     <description>Manages all UDM modules</description>
     <flavor icon="udm-users" id="users/user">
       <name>Users</name>
       <description>Managing users</description>
     </flavor>
     <categories>
       <category name="domain"/>
     </categories>
     <command name="udm/query" function="query">
     </command>
     <command name="udm/containers" function="containers">
       <attribute name="superordinate" syntax="String" required="False"/>
     </command>
   </module>
 </umc>

The *module* tag defines the basic details of a UMC module

id
	This identifier must be unique among the modules of an UMC server. Other
	files may extend the definition of a module by adding more flavors
	or categories.

icon
	The value of this attribute defines an identifier for the icon that
	should be used for the module. Details for installing icons can be
	found in the section [[#Packaging]]

The child elements *name* and *description* define the english human
readable name and description of the module. For other translations the
build tools will create translation files. Details can be found in the
section [[#Packaging]].

This example defines a so called flavor. A flavor defines a new name,
description and icon for the same UMC module. This can be used to show
several"virtual" modules in the overview of the web frontend. Additionally the flavor is passed to the UMC server with each request i.e. the UMC modul has the possibility to act differently for a specific flavor.

As the next element *categories* is defined in the example. The child
elements *category* set the categories wthin the overview where the
module should be shown. Each module can be more than one category. The
attribute name is the internal identify of category. The UMC server
brings a set of pre-defined categories:

favorites
	This category is intended to be filled by the user herself.

system
	Tools manipulating the system itself (e.g. software installation)
	shopuld go in here.

wizards
	UMC modules providing a step-by-step assistent to create some kind
	of configuration should be added to this category

monitor Everything that provides monitor functionality (e.g. simple
system statistics) should be placed in this category

At the end of the definition file a list of commands is specified. The
UMC server only passes commands to a UMC module that are defined. A
command definition has two attributes:

name
	is the name of the command that is passed to the UMC module. Within
	the UMCP message it is the first argument after the UMCP COMMAND.

function
	defines the method to be invoked within the python module when the
	command is called.

Each command can have arguments and a return value. These can also be
specified as chidl elements of the command. For example

 <attribute name="superordinate" syntax="String" required="False"/>

defines an attribute superordinate of type String that is optional. What
syntax types are support is defined in the next section.

The translations are stored in extra po files that are generated by the
UMC build tools.
"""

import copy
import os
import sys
import xml.parsers.expat
import xml.etree.ElementTree as ET

from .tools import JSON_Object, JSON_List, JSON_Dict
from .log import RESOURCES

class Attribute( JSON_Object ):
	'''Represents an command attribute'''
	def __init__( self, name = '', syntax = '', required = True ):
		self.name = name
		self.syntax = syntax
		self.required = required

	def fromJSON( self, json ):
		for attr in ( 'name' , 'syntax', 'required' ):
			setattr( self, attr, json[ attr ] )

class Command( JSON_Object ):
	'''Represents an UMCP command handled by a module'''
	SEPARATOR = '/'

	def __init__( self, name = '', method = None, attributes = None ):
		self.name = name
		if method:
			self.method = method
		else:
			self.method = self.name.replace( Command.SEPARATOR, '_' )
		if attributes is None:
			self.attributes = JSON_List()
		else:
			self.attributes = attributes

	def fromJSON( self, json ):
		for attr in ( 'name' , 'method' ):
			setattr( self, attr, json[ attr ] )
		for attr in json[ 'attributes' ]:
			attribute = Attribute()
			attribute.fromJSON( attr )
			self.attributes.append( attribute )

class Flavor( JSON_Object ):
	'''Defines a flavor of a module. This provides another name and icon
	in the overview and may influence the behaviour of the module.'''
	def __init__( self, id = '', icon = '', name = '', description = '', overwrites = [], deactivated=False, priority = -1, translationId=None ):
		self.id = id
		self.name = name
		self.description = description
		self.icon = icon
		self.overwrites = overwrites
		self.deactivated = deactivated
		self.priority = priority
		self.translationId = translationId

class Module( JSON_Object ):
	'''Represents an command attribute'''
	def __init__( self, id = '', name = '', description = '', icon = '', categories = None, flavors = None, commands = None, priority = -1 ):
		self.id = id
		self.name = name
		self.description = description
		self.icon = icon
		self.priority = priority
		if flavors is None:
			self.flavors = JSON_List()
		else:
			self.flavors = JSON_List( flavors )

		if categories is None:
			self.categories = JSON_List()
		else:
			self.categories = categories
		if commands is None:
			self.commands = JSON_List()
		else:
			self.commands = commands

	def fromJSON( self, json ):
		if isinstance( json, dict ):
			for attr in ( 'id', 'name' , 'description', 'icon', 'categories' ):
				setattr( self, attr, json[ attr ] )
			commands = json[ 'commands' ]
		else:
			commands = json
		for cmd in commands:
			command = Command()
			command.fromJSON( cmd )
			self.commands.append( command )

	def merge( self, other ):
		''' merge another Module object into current one '''
		if not self.name:
			self.name = other.name

		if not self.icon:
			self.icon = other.icon

		if not self.description:
			self.description = other.description

		for flavor in other.flavors:
			self.flavors.append(flavor)

		for category in other.categories:
			if not category in self.categories:
				self.categories.append(category)

		for command in other.commands:
			if not command in self.commands:
				self.commands.append(command)


class XML_Definition( ET.ElementTree ):
	'''container for the interface description of a module'''
	def __init__( self, root = None, filename = None ):
		ET.ElementTree.__init__( self, element = root, file = filename )

	@property
	def name( self ):
		return self.findtext( 'module/name' )

	@property
	def description( self ):
		return self.findtext( 'module/description' )

	@property
	def id( self ):
		return self.find( 'module' ).get( 'id' )

	@property
	def priority( self ):
		try:
			return float(self.find( 'module' ).get( 'priority', -1 ))
		except ValueError:
			RESOURCES.warn( 'No valid number type for property "priority": %s' % self.find( 'module' ).get('priority') )
		return None

	@property
	def translationId( self ):
		return self.find( 'module' ).get( 'translationId', '' )

	@property
	def notifier( self ):
		return self.find( 'module' ).get( 'notifier' )

	@property
	def icon( self ):
		return self.find( 'module' ).get( 'icon' )

	@property
	def flavors( self ):
		'''Retrieve list of flavor objects'''
		for elem in self.findall( 'module/flavor' ):
			flavor = Flavor( elem.get( 'id' ), elem.get( 'icon' ) )
			flavor.overwrites = elem.get( 'overwrites', '' ).split( ',' )
			flavor.deactivated = (elem.get( 'deactivated', 'no' ).lower() in ('yes','true','1'))
			flavor.translationId = self.translationId
			flavor.name = elem.findtext( 'name' )
			flavor.description = elem.findtext( 'description' )
			try:
				flavor.priority = float(elem.get('priority', -1))
			except ValueError:
				RESOURCES.warn( 'No valid number type for property "priority": %s' % elem.get('priority') )
				flavor.priority = None
			yield flavor

	@property
	def categories( self ):
		return [ elem.get( 'name' ) for elem in self.findall( 'module/categories/category' ) ]

	def commands( self ):
		'''Generator to iterate over the commands'''
		for command in self.findall( 'module/command' ):
			yield command.get( 'name' )

	def get_module( self ):
		return Module( self.id, self.name, self.description, self.icon, self.categories, self.flavors, priority = self.priority )

	def get_flavor( self, name ):
		'''Retrieves details of a flavor'''
		for flavor in self.flavors:
			if flavor.name == name:
				cmd = Flavor( name, flavor.get( 'function' ) )
				return cmd

		return None

	def get_command( self, name ):
		'''Retrieves details of a command'''
		for command in self.findall( 'module/command' ):
			if command.get( 'name' ) == name:
				cmd = Command( name, command.get( 'function' ) )
				for elem in command.findall( 'attribute' ):
					attr = Attribute( elem.get( 'name' ), elem.get( 'syntax' ), elem.get( 'required' ) in ( '', "1" ) )
					cmd.attributes.append( attr )
				return cmd
		return None

_manager = None

class Manager( dict ):
	'''Manager of all available modules'''

	DIRECTORY = os.path.join( sys.prefix, 'share/univention-management-console/modules' )
	def __init__( self ):
		dict.__init__( self )

	def modules( self ):
		'''Return list of module names'''
		return self.keys()

	def load( self ):
		'''Load the list of available modules. As the list is cleared
		before, the method can also be used for reloading'''
		RESOURCES.info( 'Loading modules ...' )
		self.clear()
		for filename in os.listdir( Manager.DIRECTORY ):
			if not filename.endswith( '.xml' ):
				continue
			try:
				mod = XML_Definition( filename = os.path.join( Manager.DIRECTORY, filename ) )
				RESOURCES.info( 'Loaded module %s' % filename )
			except xml.parsers.expat.ExpatError, e:
				RESOURCES.warn( 'Failed to load module %s: %s' % ( filename, str( e ) ) )
				continue
			# save list of definitions in self
			self.setdefault( mod.id, [] ).append(mod)

	def permitted_commands( self, hostname, acls ):
		'''Retrieves a list of all modules and commands available
		according to the ACLs (instance of LDAP_ACLs)

		{ id : Module, ... }
		'''
		RESOURCES.info( 'Retrieving list of permitted commands' )
		modules = {}
		for module_id in self:
			# get first Module and merge all subsequent Module objects into it
			mod = None
			for module_xml in self[ module_id ]:
				nextmod = module_xml.get_module()
				if mod:
					mod.merge( nextmod )
				else:
					mod = nextmod

			if not mod.flavors:
				flavors = [ Flavor( id = None ) ]
			else:
				flavors = copy.copy( mod.flavors )

			deactivated_flavors = set()
			for flavor in flavors:
				RESOURCES.info('mod=%s  flavor=%s  deactivated=%s' % (module_id, flavor.id, flavor.deactivated))
				if flavor.deactivated:
					deactivated_flavors.add(flavor.id)
					continue

				at_least_one_command = False
				# iterate over all commands in all XML descriptions
				for module_xml in self[ module_id ]:
					for command in module_xml.commands():
						if acls.is_command_allowed( command, hostname, flavor = flavor.id ):
							if not module_id in modules:
								modules[ module_id ] = mod
							cmd = module_xml.get_command( command )
							if not cmd in modules[ module_id ].commands:
								modules[ module_id ].commands.append( cmd )
							at_least_one_command = True

				# if there is not one command allowed with this flavor
				# it should not be shown in the overview
				if not at_least_one_command and mod.flavors:
					mod.flavors.remove( flavor )

			mod.flavors = JSON_List( filter( lambda f: f.id not in deactivated_flavors, mod.flavors ) )

			overwrites = set()
			for flavor in mod.flavors:
				overwrites.update( flavor.overwrites )

			mod.flavors = JSON_List( filter( lambda f: f.id not in overwrites, mod.flavors ) )

		return modules

	def module_providing( self, modules, command ):
		'''Searches a dictionary of modules (as returned by
		permitted_commands) for the given command. If found, the id of
		the module is returned, otherwise None'''
		RESOURCES.info( 'Searching for module providing command %s' % command )
		for module_id in modules:
			for cmd in modules[ module_id ].commands:
				if cmd.name == command:
					RESOURCES.info( 'Found module %s' % module_id )
					return module_id

		RESOURCES.info( 'No module provides %s' % command )
		return None

if __name__ == '__main__':
	mgr = Manager()
