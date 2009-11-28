#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name   : Exceptions.py
# Purpose: Exceptions definitions 
# Author : Henry Caballero 	<hh.caballero921@uniandes.edu.co>
#
# This product includes software derived from the Access Grid project
# <http://www.accessgrid.org>.
# 
#
#    Copyright (C) 2009
#    IMAGINE research group	<http://imagine.uniandes.edu.co>
#    Universidad de los Andes	<http://www.uniandes.edu.co>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------

__author__  = "Henry Caballero <hh.caballero921@uniandes.edu.co>"
__license__ = "GNU GPL"
__version__ = "3.0"
__revision__ = "$Id: Exceptions.py,v 1.1 2009/05/06 06:28:53 agmoxdev Exp$"

class SharedPaintException(Exception):
    """Thrown when a error occurs and it must be shown to the user."""
    pass