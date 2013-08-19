"""
@summary: Constants for the Lifemapper web service clients
@author: CJ Grady
@version: 2.1.1
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

WEBSITE_ROOT = "http://lifemapper.org"
LM_NAMESPACE = "http://lifemapper.org"
LM_CLIENT_VERSION_URL = "http://lifemapper.org/clients/versions.xml"

DEFAULT_POST_USER = "anon"
DEFAULT_USER = "lm2"

ENCODING = "utf-8"

SHAPEFILE_EXTENSIONS = ["shp", "shx", "dbf", "prj", "sbn", 
                        "sbx", "fbn", "fbx", "ain", "aih", 
                        "ixs", "mxs", "atx", "cpg"]

class JobStage:
   GENERAL = 0
   # _RadIntersectJob contains RADExperiment 
   INTERSECT = 10
   # _RadCompressJob contains original or splotch Pam 
   COMPRESS = 20
   # _RadRandomizeJob contains RADBucket and random PamSum
#   RANDOMIZE = 30
   SWAP = 31
   SPLOTCH = 32
   # _RadCalculateJob contains original or random PamSum
   CALCULATE = 40

class JobStatus:
   GENERAL = 0
   INITIALIZE = 1
   PULL_REQUESTED = 90
   PULL_COMPLETE = 100
   COMPUTE_INITIALIZED = 110
   RUNNING = 120
   COMPUTED = 130
   PUSH_REQUESTED = 140
   PUSHED = 150
   PUSH_COMPLETE = 200
   COMPLETE = 300
   
   GENERAL_ERROR = 1000
   UNKNOWN_ERROR = 1001
   MODEL_ERROR = 1002
   PUSH_FAILED = 1100
   
CONTENT_TYPES = {
                 "AAIGrid" : "text/plain",
                 "GTiff" : "image/tiff"
                }
   