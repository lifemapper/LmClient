"""
@summary: setup.py for client library for Lifemapper web services
@author: CJ Grady
@contact: cjgrady [at] ku [dot] edu
@organization: Lifemapper (http://lifemapper.org)
@version: 2.0.0
@status: release

@license: Copyright (C) 2013, University of Kansas Center for Research

          Lifemapper Project, lifemapper [at] ku [dot] edu, 
          Biodiversity Institute,
          1345 Jayhawk Boulevard, Lawrence, Kansas, 66045, USA
   
          This program is free software; you can redistribute it and/or modify 
          it under the terms of the GNU General Public License as published by 
          the Free Software Foundation; either version 2 of the License, or (at 
          your option) any later version.
  
          This program is distributed in the hope that it will be useful, but 
          WITHOUT ANY WARRANTY; without even the implied warranty of 
          MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
          General Public License for more details.
  
          You should have received a copy of the GNU General Public License 
          along with this program; if not, write to the Free Software 
          Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 
          02110-1301, USA.
"""

longDesc = """\
This is the Lifemapper Python client library used to access the Lifemapper
Species Distribution Modeling web services and new with version 2.0.0, the 
Lifemapper Range and Diversity services.

With version 2.0.0 the library functions have been grouped and moved under
sub-modules.  So species distribution web services are now under the sdm 
module and the new range and diversity services are available under rad.
"""

#from distutils.core import setup
from setuptools import setup, find_packages

setup(name="Lifemapper_Client",
      version="2.0.0",
      description="A Python client for accessing Lifemapper web services",
      author="CJ Grady",
      author_email="cjgrady@ku.edu",
      url="http://lifemapper.org",
      license="gpl",
      long_description=longDesc,
      packages=find_packages()
     )