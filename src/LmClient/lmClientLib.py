"""
@summary: Client library for Lifemapper web services
@author: CJ Grady
@contact: cjgrady [at] ku [dot] edu
@organization: Lifemapper (http://lifemapper.org)
@version: 3.1.0
@status: release

@license: Copyright (C) 2015, University of Kansas Center for Research

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

@note: Additional service documentation can be found at:
          http://lifemapper.org/schemas/services.wadl

@note: Time format - Time should be specified in ISO 8601 format 
          YYYY-mm-ddTHH-MM-SSZ
             Where:
                YYYY is the four-digit year (example 2009)
                mm is the two-digit month (example 06)
                dd is the two-digit day (example 07)
                HH is the two-digit hour (example 09)
                MM is the two-digit minute (example 23)
                SS is the two-digit second (example 15)
            Example for June 7, 2009 9:23:15 AM - 2009-06-07T09:23:15Z
"""
import cookielib
import glob
import os
import StringIO
from types import ListType
import urllib
import urllib2
import warnings
import zipfile


from LmClient.constants import LM_CLIENT_VERSION_URL
from LmClient.openTree import OTLClient
from LmClient.rad import RADClient
from LmClient.sdm import SDMClient

from LmCommon.common.lmconstants import DEFAULT_POST_USER, SHAPEFILE_EXTENSIONS
from LmCommon.common.localconstants import ARCHIVE_USER, WEBSITE_ROOT
from LmCommon.common.lmXml import deserialize, fromstring
from LmCommon.common.unicode import toUnicode

# .............................................................................
class OutOfDateException(Exception):
   """
   @summary: An out of date exception indicates that the client is out of date
                and cannot continue to operate with the current version of the
                web services.
   """
   def __init__(self, myVersion, minVersion):
      """
      @param myVersion: The current version of the client library
      @param minVersion: The minimum required version of the client library
      """
      Exception.__init__(self)
      self.myVersion = myVersion
      self.minVersion = minVersion

   def __repr__(self):
      return "Out of date exception: my version: %s, minimum version: %s" % (\
                                               self.myVersion, self.minVersion)

   def __str__(self):
      return "Out of date exception: my version: %s, minimum version: %s" % (\
                                               self.myVersion, self.minVersion)

# .............................................................................
class LMClient(object):
   """
   @summary: Lifemapper client library class
   """
   # .........................................
   def __init__(self, userId=DEFAULT_POST_USER, pwd=None, server=WEBSITE_ROOT):
      """
      @summary: Constructor
      @param userId: (optional) The id of the user to use for this session
      @param pwd: (optional) The password for the specified user
      @param server: (optional) The Lifemapper webserver address
      @note: Lifemapper RAD services are not available anonymously
      """
      self._cl = _Client(userId=userId, pwd=pwd, server=server)
      self._cl.checkVersion()
      self.sdm = SDMClient(self._cl)
      if userId not in [DEFAULT_POST_USER, ARCHIVE_USER]:
         self.rad = RADClient(self._cl)
         self.otl = OTLClient(self._cl)
   
   # .........................................
   def __del__(self):
      """
      @summary: Destructor.  Logs out for cleanup
      """
      self._cl.logout()
      
   # .........................................
   def logout(self):
      """
      @summary: Log out of a session
      @deprecated: Will be performed on object deletion
      """
      self._cl.logout()
      self._cl = None

# .............................................................................
class _Client(object):
   """
   @summary: Private Lifemapper client class
   """
   __version__ = "3.1.0"

   # .........................................
   def __init__(self, userId=DEFAULT_POST_USER, pwd=None, server=WEBSITE_ROOT):
      """
      @summary: Constructor of LMClient
      @param userId: (optional) User id to use if different from the default
                        [string]
      @param pwd: (optional) Password for optional user id. [string]
      @param server: (optional) The Lifemapper web server root address
      """
      self.userId = userId
      self.pwd = pwd
      self.server = server
      
      self.cookieJar = cookielib.LWPCookieJar()
      opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))
      urllib2.install_opener(opener)
      self._login()
   
   # .........................................
   def checkVersion(self, clientName="lmClientLib", verStr=None):
      """
      @summary: Checks the version of the client library against the versions
                   reported by the web server
      @param clientName: (optional) Check this client if not the client library
      @param verStr: (optional) The version string of the client to check
      @raise OutOfDateException: Raised if the client is out of date and 
                                    cannot continue
      """
      res = self.makeRequest(LM_CLIENT_VERSION_URL, objectify=True)
      for client in res:
         if client.name == clientName:
            minVersionStr = client.versions.minimum
            curVersionStr = client.versions.current
            minVersion = self.getVersionNumbers(verStr=minVersionStr)
            curVersion = self.getVersionNumbers(verStr=curVersionStr)
            myVersion = self.getVersionNumbers(verStr=verStr)
            
            if myVersion < minVersion:
               raise OutOfDateException(myVersion, minVersion)
            if myVersion < curVersion:
               warnings.warn("Client is not latest version: (%s < %s)" % \
                                   (myVersion, curVersion), Warning)
            
   # .........................................
   def getVersionNumbers(self, verStr=None):
      """
      @summary: Splits a version string into a tuple
      @param verStr: The version number as a string, if None, get the client 
                        version
      @return: Tuple of version (major, minor, revision, status)
      """
      if verStr is None:
         verStr = self.__version__
      major = 0
      minor = 0
      revision = 0
      status = "zzzz"
      vStr = verStr.strip().split(' ')

      if len(vStr) > 1:
         status = vStr[1]
      
      mmrList = vStr[0].split('.') # Split on '.'
      
      try: # If not all parts are specified, specifies as many as possible
         major = int(mmrList[0])
         minor = int(mmrList[1])
         revision = int(mmrList[2])
      except:
         pass
      
      return (major, minor, revision, status)
      
   # .........................................
   def autoUnzipShapefile(self, cnt, filePath, overwrite=False):
      """
      @summary: Attempt to unzip a zipped shapefile.
      @param cnt: The zipped shapefile content
      @param filePath: If a directory is specified, unzip the shapefile there.  
                          If a .zip path is specified, write out the zipfile 
                          as-is.  If a .shp path is specified, write out the 
                          shapefile files with that name as the base.
      @param overwrite: (optional) Boolean indicating if the files should be 
                           overwritten if present
      @note: If specifying a directory as the filePath, it should exist
      """
      if os.path.isdir(filePath):
         with zipfile.ZipFile(StringIO.StringIO(cnt), 'r', allowZip64=True) as zf:
            # Check to see if files exist
            nameList = zf.namelist()
            if not overwrite:
               for name in nameList:
                  if os.path.exists(os.path.join(filePath, name)):
                     raise Exception( 
                        "File %s, already exists and overwrite is: %s" % (
                                    os.path.join(filePath, name), overwrite))
            zf.extractall(filePath)
      else:
         base, ext = os.path.splitext(filePath)
         if ext == '.zip':
            with open(filePath, 'wb') as outF:
               outF.write(cnt)
         elif ext == '.shp':
            # Check to see if filePath exists
            # Able to write if path doesn't exist or overwrite is true
            if not os.path.exists(filePath) or overwrite:
               with zipfile.ZipFile(StringIO.StringIO(cnt), 'r', allowZip64=True) as zf:
                  for name in zf.namelist():
                     fCnt = zf.read(name)
                     fBase, fExt = os.path.splitext(name)
                     with open(os.path.join(filePath, '%s%s' % (base, fExt)), 'wb') as outF:
                        outF.write(fCnt)
                     
            else:
               raise Exception, "%s already exists and overwrite is: %s" % (
                                                           filePath, overwrite)
         else:
            raise Exception, "Do not know how to handle file path: %s" % filePath
   
   # .........................................
   def getAutozipShapefileStream(self, fn):
      """
      @summary: Automatically creates a zipped version of a shapefile from the
                   shapefile's .shp file.  Finds the rest of the files it needs
                   and includes them in one package
      @param fn: Path to the shapefile's .shp file
      @return: The zipped shapefile
      @rtype: String
      """
      files = []
      if fn.endswith('.shp'):
         for f in glob.iglob("%s*" % fn.strip('shp')):
            ext = os.path.splitext(f)[1]
            if ext in SHAPEFILE_EXTENSIONS:
               files.append(f)
      else:
         raise Exception ("Filename must end in '.shp'")
      
      outStream = StringIO.StringIO()
      zf = zipfile.ZipFile(outStream, 'w', allowZip64=True)
      for f in files:
         zf.write(f, os.path.basename(f))
      zf.close()
      outStream.seek(0)
      return outStream.getvalue()

   # .........................................
   def getCount(self, url, parameters=[]):
      """
      @summary: Gets the item count from a count service
      @param url: A URL pointing to a count service end-point
      @param parameters: (optional) List of query parameters for the request
      """
      obj = self.makeRequest(url, method="GET", parameters=parameters, 
                                                                objectify=True)
      count = int(obj.items.itemCount)
      return count
   
   # .........................................
   def getList(self, url, parameters=[]):
      """
      @summary: Gets a list of items from a list service
      @param url: A URL pointing to a list service end-point
      @param parameters: (optional) List of query parameters for the request
      """
      obj = self.makeRequest(url, method="GET", parameters=parameters, 
                                                                objectify=True)
      try:
         if isinstance(obj.items, ListType):
            lst = obj.items
         else:
            lst = obj.items.item
         if lst is not None:
            if not isinstance(lst, ListType):
               lst = [lst]
            return lst
      except Exception:
         #print e
         pass
      return []

   # .........................................
   def makeRequest(self, url, method="GET", parameters=[], body=None, 
                         headers={}, objectify=False):
      """
      @summary: Performs an HTTP request
      @param url: The url endpoint to make the request to
      @param method: (optional) The HTTP method to use for the request
      @param parameters: (optional) List of url parameters
      @param body: (optional) The payload of the request
      @param headers: (optional) Dictionary of HTTP headers
      @param objectify: (optional) Should the response be turned into an object
      @return: Response from the server
      """
      parameters = removeNonesFromTupleList(parameters)
      urlparams = urllib.urlencode(parameters)
      
      if body is None and len(parameters) > 0 and method.lower() == "post":
         body = urlparams
      else:
         url = "%s?%s" % (url, urlparams)
      req = urllib2.Request(url, data=body, headers=headers)
      req.add_header('User-Agent', 'LMClient/%s (Lifemapper Python Client Library; http://lifemapper.org; lifemapper@ku.edu)' % self.__version__)
      try:
         ret = urllib2.urlopen(req)
      except urllib2.HTTPError, e:
         #print e.headers['Error-Message']
         raise e
      except Exception, e:
         raise Exception( 'Error returning from request to %s (%s)' % (url, toUnicode(e)))
      else:
         resp = ''.join(ret.readlines())
         if objectify:
            return self.objectify(resp)
         else:
            return resp

   # .........................................
   def objectify(self, xmlString):
      """
      @summary: Takes an XML string and processes it into a python object
      @param xmlString: The xml string to turn into an object
      @note: Uses LmAttList and LmAttObj
      @note: Object attributes are defined on the fly
      """
      return deserialize(fromstring(xmlString))   

   # .........................................
   def _login(self):
      """
      @summary: Attempts to log a user in
      @todo: Handle login failures
      """
      if self.userId != DEFAULT_POST_USER and self.userId != ARCHIVE_USER and \
                        self.pwd is not None:
         url = "%s/login" % self.server
         
         urlParams = [("username", self.userId), ("pword", self.pwd)]
         
         self.makeRequest(url, parameters=urlParams)

   # .........................................
   def logout(self):
      """
      @summary: Logs the user out
      """
      url = '/'.join((self.server, "logout"))
      self.makeRequest(url)

# =============================================================================
# =                             Helper Functions                              =
# =============================================================================
# .............................................................................
def removeNonesFromTupleList(paramsList):
   """
   @summary: Removes parameter values that are None
   @param paramsList: List of parameters (name, value) [list of tuples]
   @return: List of parameters that are not None [list of tuples]
   """
   ret = []
   for param in paramsList:
      if param[1] is not None:
         ret.append(param)
   return ret

# .............................................................................
def stringifyError(err):
   """
   @summary: This really only adds information for urllib2.HTTPErrors that 
                include an 'Error-Message' header
   @param err: The exception to stringify
   """
   try:
      return err.hdrs['Error-Message']
   except:
      return toUnicode(err)
