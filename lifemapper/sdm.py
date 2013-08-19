"""
@summary: Module containing client functions for interacting with Lifemapper
             Species Distribution Modeling services
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
from collections import namedtuple

from constants import CONTENT_TYPES

# .............................................................................
class AlgorithmParameter(object):
   """
   @summary: Algorithm parameter class
   """
   def __init__(self, name, pType, pDefault=None, pMin=None, pMax=None, 
                                                                  pValue=None):
      """
      @summary: Constructor
      @param name: The name of the algorithm parameter
      @param pType: The type of the parameter (integer, string, float, etc)
      @param pDefault: (optional) The default value of the parameter
      @param pMin: (optional) The minimum value of the parameter
      @param pMax: (optional) The maximum value of the parameter
      @param pValue: (optional) The value of the parameter
      """
      self.name = name
      self.type = pType
      self.default = pDefault
      self.min = pMin
      self.max = pMax
      self.value = pValue if pValue is not None else self.default
      
# .............................................................................
class Algorithm(object):
   """
   @summary: Algorithm class
   """
   def __init__(self, clAlg):
      """
      @summary: Constructor
      @param clAlg: Client library algorithm object
      """
      self.code = clAlg.code
      self.name = clAlg.name
      self.parameters = []
      for param in clAlg.parameters:
         try:
            pMin = param.min
         except:
            pMin = None
            
         try:
            pMax = param.max
         except:
            pMax = None
             
         p = AlgorithmParameter(param.name, param.type, pDefault=param.default,
                                pMin=pMin, pMax=pMax)
         self.parameters.append(p)
         
# .............................................................................
class SDMClient(object):
   """
   @summary: Lifemapper SDM web service functions
   """
   # .........................................
   def __init__(self, cl):
      """
      @summary: Constructor
      @param cl: Lifemapper client for connection to web services
      """
      self.cl = cl
      self.algos = self._getAlgorithms()

   # .........................................
   def _getAlgorithms(self):
      """
      @summary: Gets available Lifemapper SDM algorithms
      @return: Lifemapper algorithms
      """
      url = "%s/clients/algorithms.xml" % self.cl.server
      obj = self.cl.makeRequest(url, method="GET", objectify=True)
      return obj
   
   # .........................................
   def getAlgorithmFromCode(self, code):
      """
      @summary: Deep copies an algorithm object and adds a value attribute to 
                   each parameter that is populated with the default value for
                   that parameter
      @param code: The code of the algorithm to return
      """
      alg = None
      for algo in self.algos:
         if algo.code.lower() == code.lower():
            alg = algo
            break
      if alg is not None:
         a = Algorithm(alg)
      else:
         raise Exception("Algorithm code: %s was not recognized" % str(code))
      return a
   
   # --------------------------------------------------------------------------
   # ===============
   # = Experiments =
   # ===============
   # .........................................
   def countExperiments(self, afterTime=None, beforeTime=None, 
                              displayName=None, epsgCode=None, 
                              algorithmCode=None, occurrenceSetId=None, 
                              status=None, public=False):
      """
      @summary: Counts the number of experiments that match the specified 
                   criteria.
      @param afterTime: (optional) Count only experiments modified after this 
                           time.  See time formats in the module documentation.
                           [integer or string]
      @param beforeTime: (optional) Count only experiments modified before this 
                           time.  See time formats in the module documentation.
                           [integer or string]
      @param displayName: (optional) Count only experiments with this display
                             name. [string]
      @param epsgCode: (optional) Count only experiments with this EPSG code 
                          [integer]
      @param algorithmCode: (optional) Count only experiments generated with 
                               this algorithm code.  See available algorithms 
                               in the module documentation. [string]
      @param occurrenceSetId: (optional) Count only experiments generated from
                                 this occurrence set. [integer]
      @param status: (optional) Count only experiments with this model status.
                        More information about status is available in the 
                        module documentation. [integer]
      @param public: (optional) If True, use the anonymous client if available
      @return: The total number of experiments that match the given criteria.
                  [integer]
      """
      url = "%s/services/sdm/experiments/" % self.cl.server
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("displayName", displayName),
                ("epsgCode", epsgCode),
                ("algorithmCode", algorithmCode),
                ("occurrenceSetId", occurrenceSetId),
                ("status", status),
                ("public", int(public))
               ]
      count = self.cl.getCount(url, params)
      return count
   
   # .........................................
   def getExperiment(self, expId):
      """
      @summary: Gets a Lifemapper experiment
      @param expId: The id of the experiment to be returned. [integer]
      @return: A Lifemapper experiment [LmAttObj]
      """
      url = "%s/services/sdm/experiments/%s" % (self.cl.server, expId)
      obj = self.cl.makeRequest(url, method="GET", objectify=True).experiment
      return obj
    
   # .........................................
   def listExperiments(self, afterTime=None, beforeTime=None, displayName=None, 
                             epsgCode=None, perPage=100, page=0, 
                             algorithmCode=None, occurrenceSetId=None, 
                             status=None, public=False, fullObjects=False):
      """
      @summary: Lists experiments that meet the specified criteria.
      @param afterTime: (optional) Return only experiments modified after this 
                           time.  See time formats in the module documentation. 
                           [integer or string]
      @param beforeTime: (optional) Return only experiments modified before 
                            this time.  See time formats in the module 
                            documentation. [integer or string]
      @param displayName: (optional) Return only experiments with this display
                             name. [string]
      @param epsgCode: (optional) Return only experiments that use this EPSG 
                          code. [integer]
      @param perPage: (optional) Return this many results per page. [integer]
      @param page: (optional) Return this page of results. [integer]
      @param algorithmCode: (optional) Return only experiments generated from 
                               this algorithm.  See available algorithms in the
                               module documentation. [string]
      @param occurrenceSetId: (optional) Return only experiments generated from
                                 this occurrence set. [integer]
      @param status: (optional) Return only experiments with this status.  More
                        information about status can be found in the module
                        documentation. [integer]
      @param public: (optional) If True, use the anonymous client if available
      @param fullObjects: (optional) If True, return the full objects instead
                             of the list objects
      @return: Experiments that match the specified parameters. [LmAttObj]
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("displayName", displayName),
                ("espgCode", epsgCode),
                ("algorithmCode", algorithmCode),
                ("occurrenceSetId", occurrenceSetId),
                ("status", status),
                ("page", page),
                ("perPage", perPage),
                ("public", int(public)),
                ("fullObjects", int(fullObjects))
               ]
      url = "%s/services/sdm/experiments/" % self.cl.server
      items = self.cl.getList(url, parameters=params)
      return items
   
   # .........................................
   def postExperiment(self, algorithm, mdlScn, occSetId, prjScns=[], 
                            mdlMask=None, prjMask=None, 
                            email=None, name=None, description=None):
      """
      @summary: Post a new Lifemapper experiment
      @param algorithm: An Lifemapper SDM algorithm object 
      @param mdlScn: The id of the model scenario to use for the experiment
                        [integer]
      @param occSetId: The id of the occurrence set to be used for the 
                          experiment. [integer]
      @param prjScns: (optional) List of projection scenario ids to use for the 
                         experiment [list of integers]
      @param mdlMask: (optional) A layer id mask to use when looking at the 
                         input climate layers of the model [integer]
      @param prjMask: (optional) A layer id mask to use when projecting onto a 
                         new set of climate layers [integer]
      @param email: (optional) Lifemapper will send a notification email to 
                       this address when the experiment has completed
      @param name: (optional) A name for this experiment
      @param description: (optional) A description for this experiment
      @return: Experiment
      """
      try:
         algorithmParameters = algorithm.parameters
         algoCode = algorithm.code
      except:
         algoCode = algorithm
         algorithmParameters = []
      algoParams = """\
                  <lm:parameters>
                     {params}
                  </lm:parameters>
""".format(params='\n                     '.join(
                     ["<lm:{name}>{value}</lm:{name}>".format(
                                        name=param.name, value=param.value) \
                                     for param in algorithmParameters])) \
                                        if len(algorithmParameters) > 0 else ""
      mMask = "            <lm:modelMask>%s</lm:modelMask>" % mdlMask if mdlMask is not None else ""
      pMask = "            <lm:projectionMask>%s</lm:projectionMask>" % prjMask if prjMask is not None else ""
      emailSection = "            <lm:email>%s</lm:email>" % email if email is not None else ""
      nameSection = "            <lm:name>%s</lm:name>" % name if name is not None else ""
      descSection = "            <lm:description>%s</lm:description>" % description if description is not None else ""
      prjSection = '\n'.join(([
          "            <lm:projectionScenario>{scnId}</lm:projectionScenario>".format(scnId=scnId) for scnId in prjScns]))
      postXml = """\
      <lm:request xmlns:lm="http://lifemapper.org"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:schemaLocation="http://lifemapper.org 
                                               /schemas/serviceRequest.xsd">
            <lm:experiment>
               <lm:algorithm>
                  <lm:algorithmCode>{algorithmCode}</lm:algorithmCode>
{algoParams}
               </lm:algorithm>
               <lm:occurrenceSetId>{occSetId}</lm:occurrenceSetId>
               <lm:modelScenario>{mdlScn}</lm:modelScenario>
{mMask}
{email}
{name}
{description}
{projections}
{pMask}
            </lm:experiment>
         </lm:request>""".format(algorithmCode=algoCode, 
                                 algoParams=algoParams, occSetId=occSetId, 
                                 mdlScn=mdlScn, mMask=mMask, email=emailSection, 
                                 projections=prjSection, pMask=pMask,
                                 name=nameSection, description=descSection)
      url = "%s/services/sdm/experiments/" % self.cl.server
      obj = self.cl.makeRequest(url, 
                                method="POST", 
                                body=postXml, 
                                headers={"Content-Type": "application/xml"},
                                objectify=True).experiment
      return obj
   
   # --------------------------------------------------------------------------
   # ==========
   # = Layers =
   # ==========
   # .........................................
   def countLayers(self, afterTime=None, beforeTime=None, epsgCode=None,
                         scenarioId=None, typeCode=None, public=False):
      """
      @summary: Counts the number of layers that match the specified criteria.
      @param afterTime: (optional) Count only layers modified after this time.  
                           See time formats in the module documentation. 
                           [integer or string]
      @param beforeTime: (optional) Count only layers modified before this 
                            time.  See time formats in the module 
                            documentation. [integer or string]
      @param epsgCode: (optional) Return only layers with this epsg code. 
                          [integer]
      @param scenarioId: (optional) Return only layers that belong to this 
                            scenario. [integer]
      @param typeCode: (optional) Return only layers that have this type code. 
                          [string]
      @param public: (optional) If True, use the anonymous client if available
      @return: The total number of layers that match the given criteria. 
                  [integer]
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("epsgCode", epsgCode),
                ("scenarioId", scenarioId),
                ("typeCode", typeCode),
                ("public", int(public))
               ]
      url = "%s/services/sdm/layers/" % self.cl.server
      count = self.cl.getCount(url, params)
      return count
   
   # .........................................
   def getLayer(self, lyrId):
      """
      @summary: Gets a Lifemapper layer
      @param lyrId: The id of the layer to be returned. [integer]
      @return: A Lifemapper layer 
      """
      url = "%s/services/sdm/layers/%s" % (self.cl.server, lyrId)
      obj = self.cl.makeRequest(url, method="GET", objectify=True).layer
      return obj

   # .........................................
   def getLayerKML(self, lyrId, filename=None):
      """
      @summary: Gets a Lifemapper layer as a kml file
      @param lyrId: The id of the layer to be returned. [integer]
      @param filename: (optional) The location to save the resulting file, if
                          None, the string is returned
      @note: This function will be removed in a later version in favor of 
                specifying the format when making the get request
      @raise Exception: Raised if write fails
      """
      url = "%s/services/sdm/layers/%s/kml" % (self.cl.server, lyrId)
      cnt = self.cl.makeRequest(url, method="GET")
      if filename is not None:
         f = open(filename, 'w')
         f.write(cnt)
         f.close()
         return None
      else:
         return cnt

   # .........................................
   def getLayerTiff(self, lyrId, filename=None):
      """
      @summary: Gets a Lifemapper layer as a tiff file
      @param lyrId: The id of the layer to be returned. [integer]
      @param filename: (optional) The location to save the resulting file, if
                          None, the string is returned
      @note: This function will be removed in a later version in favor of 
                specifying the format when making the get request
      @raise Exception: Raised if write fails
      """
      url = "%s/services/sdm/layers/%s/tiff" % (self.cl.server, lyrId)
      cnt = self.cl.makeRequest(url, method="GET")
      if filename is not None:
         f = open(filename, 'w')
         f.write(cnt)
         f.close()
         return None
      else:
         return cnt

   # .........................................
   def listLayers(self, afterTime=None, beforeTime=None, epsgCode=None,
                        perPage=100, page=0, scenarioId=None, typeCode=None,
                        public=False, fullObjects=False):
      """
      @summary: Lists layers that meet the specified criteria.
      @param afterTime: (optional) Return only layers modified after this time.  
                           See time formats in the module documentation. 
                           [integer or string]
      @param beforeTime: (optional) Return only layers modified before this 
                            time.  See time formats in the module 
                            documentation. [integer or string]
      @param epsgCode: (optional) Return only layers with this epsg code. 
                          [integer]
      @param perPage: (optional) Return this many results per page. [integer]
      @param page: (optional) Return this page of results. [integer]
      @param scenarioId: (optional) Return only layers that belong to this 
                            scenario. [integer]
      @param typeCode: (optional) Return only layers that have this type code. 
                          [string]
      @param public: (optional) If True, use the anonymous client if available
      @param fullObjects: (optional) If True, return the full objects instead
                             of the list objects
      @return: Layers that match the specified parameters. [LmAttObj]
      @note: Returned object has metadata included.  Reference items with 
                "items.item" property
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("epsgCode", epsgCode),
                ("scenarioId", scenarioId),
                ("page", page),
                ("perPage", perPage),
                ("typeCode", typeCode),
                ("public", int(public)),
                ("fullObjects", int(fullObjects))
               ]
      url = "%s/services/sdm/layers/" % self.cl.server
      items = self.cl.getList(url, parameters=params)
      return items
   
   # .........................................
   def postLayer(self, name, epsgCode, envLayerType, units, dataFormat,
                       fileName=None, layerUrl=None, layerContent=None, 
                       title=None, valUnits=None, startDate=None, endDate=None, 
                       resolution=None, keywords=[], description=None, 
                       isCategorical=False):
      """
      @summary: Posts an environmental layer
      @param name: The name of the layer
      @param epsgCode: The EPSG code for the layer
      @param envLayerType: Identifier of the layer type
      @param units: The cell size units
      @param dataFormat: Indicates what format the data is in.  Must be one of 
                            the formats at: 
                            http://www.gdal.org/formats_list.html
      @param fileName: (optional) The full path to the local file to be 
                          uploaded.  Either fileName, layerUrl, or layerContent
                          must be specified.
      @param layerUrl: (optional) A URL pointing to the raster file to be
                          uploaded.  Either fileName, layerUrl, or layerContent 
                          must be specified.
      @param layerContent: (optional) The layer data as a string.  Either 
                              fileName, layerUrl, or layerContent must be
                              specified.
      @param title: (optional) A longer title of the layer
      @param valUnits: (optional) The units for the values of the raster layer
      @param startDate: (optional) The start date for the layer.  See time
                           formats in module documentation
      @param endDate: (optional) The end date for the layer.  See time formats
                         in module documentation
      @param resolution: (optional) The resolution of the cells
      @param keywords: (optional) A list of keywords to associate with the layer
      @param description: (optional) A longer description of what this layer is
      @param isCategorical: (optional) Indicates if the layer contains 
                               categorical data
      @raise Exception: Raised if none of layerUrl, layerContent, or filename 
                           are provided
      """
      params = [
                ("name", name),
                ("title", title),
                ("valUnits", valUnits),
                ("startDate", startDate),
                ("endDate", endDate),
                ("units", units),
                ("resolution", resolution),
                ("epsgCode", epsgCode),
                ("envLayerType", envLayerType),
                ("description", description),
                ("dataFormat", dataFormat),
                ("isCategorical", isCategorical)
               ]
      for kw in keywords:
         params.append(("keyword", kw))
         
      if fileName is not None:
         body = open(fileName).read()
         headers={"Content-Type" : CONTENT_TYPES[dataFormat]}
      elif layerContent is not None:
         body = layerContent
         headers={"Content-Type" : CONTENT_TYPES[dataFormat]}
      elif layerUrl is not None:
         body = None
         headers = {}
         params.append(("layerUrl", layerUrl))
      else:
         raise Exception, "Must either specify a file to upload or a url to a file when posting a layer"
         
      url = "%s/services/sdm/layers" % self.cl.server
      obj = self.cl.makeRequest(url, 
                                method="POST", 
                                parameters=params, 
                                body=body, 
                                headers=headers, 
                                objectify=True).layer
      return obj
      
   # --------------------------------------------------------------------------
   # ===================
   # = Occurrence Sets =
   # ===================
   # .........................................
   def countOccurrenceSets(self, afterTime=None, beforeTime=None, 
                                 displayName=None, epsgCode=None, 
                                 minimumNumberOfPoints=None, public=False):
      """
      @summary: Counts the number of occurrence sets that match the specified
                   criteria.
      @param afterTime: (optional) Count only occurrence sets modified after 
                           this time.  See time formats in the module 
                           documentation. [integer or string]
      @param beforeTime: (optional) Count only occurrence sets modified before 
                            this time.  See time formats in the module 
                            documentation. [integer or string]
      @param displayName: (optional) Count only occurrence sets that have this 
                             display name. [string]
      @param epsgCode: (optional) Count only occurrence sets that use this 
                          EPSG code. [integer]
      @param minimumNumberOfPoints: (optional) Count only occurrence sets that 
                                       have at least this many points. 
                                       [integer]
      @param public: (optional) If True, use the anonymous client if available
      @return: The total number of occurrence sets that match the given 
                  criteria. [integer]
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("displayName", displayName),
                ("epsgCode", epsgCode),
                ("minimumNumberOfPoints", minimumNumberOfPoints),
                ("public", int(public))
               ]
      url = "%s/services/sdm/occurrences/" % self.cl.server
      count = self.cl.getCount(url, params)
      return count
   
   # .........................................
   def getOccurrenceSet(self, occId):
      """
      @summary: Gets a Lifemapper occurrence set
      @param occId: The id of the occurrence set to be returned. [integer]
      @return: A Lifemapper occurrence set. 
      """
      url = "%s/services/sdm/occurrences/%s" % (self.cl.server, occId)
      obj = self.cl.makeRequest(url, method="GET", objectify=True).occurrence
      return obj
   
   # .........................................
   def getOccurrenceSetKML(self, occId, filename=None):
      """
      @summary: Gets a Lifemapper occurrence set as a kml file
      @param occId: The id of the occurrence set to get. [integer]
      @param filename: (optional) The name of the file location to save the 
                          output. [string]  If it is not provided the content 
                          will be returned as a string
      @note: This function will be removed in a later version in favor of 
                specifying the format when making the get request
      """
      url = "%s/services/sdm/occurrences/%s/kml" % (self.cl.server, occId)
      cnt = self.cl.makeRequest(url, method="GET")
      if filename is not None:
         f = open(filename, 'w')
         f.write(cnt)
         f.close()
         return None
      else:
         return cnt
   
   # .........................................
   def getOccurrenceSetShapefile(self, occId, filename=None):
      """
      @summary: Gets a Lifemapper occurrence set as a shapefile
      @param occId: The id of the occurrence set to get. [integer]
      @param filename: (optional) The name of the file location to save the 
                          output. [string]  If it is not provided the content 
                          will be returned as a string
      @note: This function will be removed in a later version in favor of 
                specifying the format when making the get request
      """
      url = "%s/services/sdm/occurrences/%s/shapefile" % (self.cl.server, occId)
      cnt = self.cl.makeRequest(url, method="GET")
      if filename is not None:
         f = open(filename, 'w')
         f.write(cnt)
         f.close()
         return None
      else:
         return cnt
   
   # .........................................
   def listOccurrenceSets(self, afterTime=None, beforeTime=None, 
                                perPage=100, page=0, displayName=None, 
                                epsgCode=None,
                                minimumNumberOfPoints=None, public=False, 
                                fullObjects=False):
      """
      @summary: Lists occurrence sets that meet the specified criteria.
      @param afterTime: (optional) Return only occurrence sets modified after 
                           this time.  See time formats in the module 
                           documentation. [integer or string]
      @param beforeTime: (optional) Return only occurrence sets modified before 
                            this time.  See time formats in the module 
                            documentation. [integer or string]
      @param epsgCode: (optional) Return only occurrence sets that use this 
                          EPSG code. [integer]
      @param perPage: (optional) Return this many results per page. [integer]
      @param page: (optional) Return this page of results. [integer]
      @param displayName: (optional) Return only occurrence sets that have this 
                             display name. [string]
      @param minimumNumberOfPoints: (optional) Return only occurrence sets that
                                       have at least this many points. 
                                       [integer]
      @param public: (optional) If True, use the anonymous client if available
      @param fullObjects: (optional) If True, return the full objects instead
                             of the list objects
      @return: Occurrence Sets that match the specified parameters. [LmAttObj]
      @note: Returned object has metadata included.  Reference items with 
                "items.item" property
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("displayName", displayName),
                ("epsgCode", epsgCode),
                ("minimumNumberOfPoints", minimumNumberOfPoints),
                ("page", page),
                ("perPage", perPage),
                ("public", int(public)),
                ("fullObjects", int(fullObjects))
               ]
      url = "%s/services/sdm/occurrences/" % self.cl.server
      items = self.cl.getList(url, parameters=params)
      return items
   
   # .........................................
   def postOccurrenceSet(self, displayName, fileType, fileName, epsgCode=4326):
      """
      @summary: Post a new Lifemapper occurrence set
      @param displayName: The display name for the occurrence set
      @param fileType: The type of the file to upload
      @param fileName: The name of the file to upload
      @param epsgCode: (optional) The EPSG code of the occurrence data
      @return: The occurrence set id number. [integer]
      """
      parameters = [("pointsType", fileType),
                    ("displayName", displayName),
                    ("epsgCode", epsgCode)]

      if fileType.lower() == "csv":
         contentType = "text/csv"
      elif fileType.lower() == "shapefile":
         contentType = "application/x-gzip"
      else:
         raise Exception, "Unknown file type"
      
      if fileType.lower() == "shapefile":
         if fileName.endswith('.zip'):
            postBody = open(fileName).read()
         else:
            postBody = self.cl.getAutozipShapefileStream(fileName)
      else:
         f = open(fileName)
         postBody = ''.join(f.readlines())
         f.close()
      
      url = "%s/services/sdm/occurrences" % self.cl.server
      obj = self.cl.makeRequest(url, 
                                method="POST", 
                                parameters=parameters, 
                                body=postBody, 
                                headers={"Content-Type": contentType}, 
                                objectify=True).occurrence
      return obj
      
   
   # --------------------------------------------------------------------------
   # ===============
   # = Projections =
   # ===============
   # .........................................
   def countProjections(self, afterTime=None, beforeTime=None,
                              displayName=None, epsgCode=None,
                              algorithmCode=None, expId=None, 
                              occurrenceSetId=None, scenarioId=None,
                              status=None, public=False):
      """
      @summary: Counts the number of projections that match the specified
                   criteria.
      @param afterTime: (optional) Count only projections modified after this 
                           time.  See time formats in the module documentation.
                           [integer or string]
      @param beforeTime: (optional) Count only projections modified before this 
                            time.  See time formats in the module 
                            documentation. [integer or string]
      @param displayName: (optional) Count only projections with this display 
                             name. [string]
      @param epsgCode: (optional) Count only projections that use this EPSG 
                          code. [integer]
      @param algorithmCode: (optional) Count only projections that have this 
                               algorithm code.  See available algorithms in the 
                               module documentation. [string]
      @param expId: (optional) Count only projections generated from this 
                         experiment. [integer]
      @param occurrenceSetId: (optional) Count only experiments generated from 
                                 this occurrence set. [integer]
      @param status: (optional) Count only projections with this status. More
                        information about status can be found in the module 
                        documentation. [integer]
      @param public: (optional) If True, use the anonymous client if available
      @return: The total number of projections that match the given criteria.
                  [integer]
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("displayName", displayName),
                ("epsgCode", epsgCode),
                ("algorithmCode", algorithmCode),
                ("modelId", expId),
                ("occurrenceSetId", occurrenceSetId),
                ("scenarioId", scenarioId),
                ("status", status),
                ("public", int(public))
               ]
      url = "%s/services/sdm/projections/" % self.cl.server
      count = self.cl.getCount(url, params)
      return count
   
   # .........................................
   def getProjection(self, prjId):
      """
      @summary: Gets a Lifemapper projection
      @param prjId: The id of the projection to be returned. [integer]
      @return: A Lifemapper projection.
      """
      url = "%s/services/sdm/projections/%s" % (self.cl.server, prjId)
      obj = self.cl.makeRequest(url, method="GET", objectify=True).projection
      return obj
   
   # .........................................
   def getProjectionKML(self, prjId, filename=None):
      """
      @summary: Gets a Lifemapper projection as a kml file
      @param prjId: The id of the projection to be returned. [integer]
      @param filename: (optional) The location to save the resulting file, if 
                          None, return the content of the response
      @raise Exception: Raised if write fails
      @note: This function will be removed in a later version in favor of 
                specifying the format when making the get request
      """
      url = "%s/services/sdm/projections/%s/kml" % (self.cl.server, prjId)
      cnt = self.cl.makeRequest(url, method="GET")
      if filename is not None:
         f = open(filename, 'w')
         f.write(cnt)
         f.close()
         return None
      else:
         return cnt

   # .........................................
   def getProjectionTiff(self, prjId, filename=None):
      """
      @summary: Gets a Lifemapper projection as a tiff file
      @param prjId: The id of the projection to be returned. [integer]
      @param filename: (optional) The location to save the resulting file, if 
                          None, return the content of the response
      @raise Exception: Raised if write fails
      @note: This function will be removed in a later version in favor of 
                specifying the format when making the get request
      """
      url = "%s/services/sdm/projections/%s/tiff" % (self.cl.server, prjId)
      cnt = self.cl.makeRequest(url, method="GET")
      if filename is not None:
         f = open(filename, 'w')
         f.write(cnt)
         f.close()
         return None
      else:
         return cnt

   # .........................................
   def getProjectionUrl(self, prjId, frmt=""):
      """
      @summary: Gets the url for returning a projection in the desired format
      @param prjId: The projection to return
      @param frmt: (optional) The format to return the projection in
      @return: A url pointing to the desired interface for the projection
      @todo: Check that the url is valid
      """
      url = "%s/services/sdm/projections/%s/%s" % (self.cl.server, prjId, frmt)
      return url
   
   # .........................................
   def listProjections(self, afterTime=None, beforeTime=None, displayName=None,
                             epsgCode=None, perPage=100, page=0, 
                             algorithmCode=None, expId=None, 
                             occurrenceSetId=None, scenarioId=None,
                             status=None, public=False, fullObjects=False):
      """
      @summary: Lists projections that meet the specified criteria.
      @param afterTime: (optional) Return only projections modified after this 
                           time.  See time formats in the module documentation. 
                           [integer or string]
      @param beforeTime: (optional) Return only projections modified before 
                            this time.  See time formats in the module 
                            documentation. [integer or string]
      @param displayName: (optional) Return only projections with this display
                             name. [string]
      @param epsgCode: (optional) Return only projections that use this EPSG 
                          code. [integer]
      @param perPage: (optional) Return this many results per page. [integer]
      @param page: (optional) Return this page of results. [integer]
      @param algorithmCode: (optional) Return only projections that are 
                               generated from models generated from this 
                               algorithm.  See available algorithms in the 
                               module documentation. [string]
      @param expId: (optional) Return only projections generated from this
                         experiment. [integer]
      @param occurrenceSetId: (optional) Return only projections generated from
                                 models that used this occurrence set. 
                                 [integer]
      @param scenarioId: (optional) Only return projections that use this 
                            scenario [integer]
      @param status: (optional) Return only projections that have this status. 
                        More information about status can be found in the 
                        module documentation. [integer]
      @param public: (optional) If True, use the anonymous client if available
      @param fullObjects: (optional) If True, return the full objects instead
                             of the list objects
      @return: Projections that match the specified parameters. [LmAttObj]
      @note: Returned object has metadata included.  Reference items with 
                "items.item" property
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("displayName", displayName),
                ("epsgCode", epsgCode),
                ("algorithmCode", algorithmCode),
                ("modelId", expId),
                ("occurrenceSetId", occurrenceSetId),
                ("scenarioId", scenarioId),
                ("status", status),
                ("page", page),
                ("perPage", perPage),
                ("public", int(public)),
                ("fullObjects", int(fullObjects))
               ]
      url = "%s/services/sdm/projections/" % self.cl.server
      items = self.cl.getList(url, parameters=params)
      return items
   
   # --------------------------------------------------------------------------
   # =============
   # = Scenarios =
   # =============
   # .........................................
   def countScenarios(self, afterTime=None, beforeTime=None, epsgCode=None,
                         keyword=[], matchingScenario=None, public=False):
      """
      @summary: Counts the number of scenarios that match the specified 
                   criteria.
      @param afterTime: (optional) Count only scenarios modified after this 
                           time.  See time formats in the module documentation.
                           [integer or string]
      @param beforeTime: (optional) Count only scenarios modified before this 
                            time.  See time formats in the module 
                            documentation. [integer or string]
      @param epsgCode: (optional) Count only scenarios that use this EPSG code. 
                          [integer]
      @param keyword: (optional) Count only scenarios that have the keywords in 
                         this list. [list of strings]
      @param matchingScenario: (optional) Count only scenarios that match this 
                                  scenario. [integer]
      @param public: (optional) If True, use the anonymous client if available
      @return: The number of scenarios that match the supplied criteria.
                  [integer]
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("epsgCode", epsgCode),
                ("matchingScenario", matchingScenario),
                ("public", int(public))
               ]
      for kw in keyword:
         params.append(("keyword", kw))
      url = "%s/services/sdm/scenarios/" % self.cl.server
      count = self.cl.getCount(url, params)
      return count
   
   # .........................................
   def getScenario(self, scnId):
      """
      @summary: Gets a Lifemapper scenario
      @param scnId: The id of the scenario to be returned. [integer]
      @return: A Lifemapper scenario.
      """
      url = "%s/services/sdm/scenarios/%s" % (self.cl.server, scnId)
      obj = self.cl.makeRequest(url, method="GET", objectify=True).scenario
      return obj
   
   # .........................................
   def listScenarios(self, afterTime=None, beforeTime=None, epsgCode=None,
                           perPage=100, page=0, keyword=[], 
                           matchingScenario=None, public=False, 
                           fullObjects=False):
      """
      @summary: Lists scenarios that meet the specified criteria.
      @param afterTime: (optional) Return only scenarios modified after this 
                           time.  See time formats in the module documentation. 
                           [integer or string]
      @param beforeTime: (optional) Return only scenarios modified before this 
                            time.  See time formats in the module 
                            documentation. [integer or string]
      @param epsgCode: (optional) Return only scenarios that use this EPSG 
                          code. [integer]
      @param perPage: (optional) Return this many results per page. [integer]
      @param page: (optional) Return this page of results. [integer]
      @param keyword: (optional) Return only scenarios that have the keywords 
                         in this list. [list of strings]
      @param matchingScenario: (optional) Return only scenarios that match this
                                  scenario. [integer]
      @param public: (optional) If True, use the anonymous client if available
      @param fullObjects: (optional) If True, return the full objects instead
                             of the list objects
      @return: Scenarios that match the specified parameters. [LmAttObj]
      @note: Returned object has metadata included.  Reference items with 
                "items.item" property
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("epsgCode", epsgCode),
                ("matchingScenario", matchingScenario),
                ("page", page),
                ("perPage", perPage),
                ("public", int(public)),
                ("fullObjects", int(fullObjects))
               ]
      for kw in keyword:
         params.append(("keyword", kw))
      url = "%s/services/sdm/scenarios/" % self.cl.server
      items = self.cl.getList(url, parameters=params)
      return items
   
   # .........................................
   def postScenario(self, layers, code, epsgCode, units, title=None, 
                          author=None, description=None, startDate=None, 
                          endDate=None, resolution=None, keywords=[]):
      """
      @summary: Posts a climate scenario to the Lifemapper web services
      @param layers: A list of layer ids that should be included in this 
                        scenario
      @param code: The code to associate with this layer
      @param epsgCode: The EPSG code representing the coordinate system 
                          projection of the scenario
      @param units: The units for the cell sizes of the scenario
      @param title: (optional) A title for this scenario
      @param author: (optional) The author of this scenario
      @param description: (optional) A longer description of what this climate 
                             scenario is and what it contains
      @param startDate: (optional) The start date for this scenario.  See more
                           information about time formats in module 
                           documentation.
      @param endDate: (optional) The end date for this scenario.  See more 
                         information about time formats in module documentation
      @param resolution: (optional) The resolution of the cells
      @param keywords: (optional) A list of keywords to associate with the 
                          scenario
      """
      params = [
                ("code", code),
                ("title", title),
                ("author", author),
                ("description", description),
                ("startDate", startDate),
                ("endDate", endDate),
                ("units", units),
                ("resolution", resolution),
                ("epsgcode", epsgCode)
               ]
      for kw in keywords:
         params.append(("keyword", kw))
         
      for lyr in layers:
         params.append(("layer", lyr))
      url = "%s/services/sdm/scenarios" % self.cl.server
      
      obj = self.cl.makeRequest(url, 
                                method="post", 
                                parameters=params,
                                objectify=True).scenario
      return obj
   
   # --------------------------------------------------------------------------
   # ==============
   # = Type Codes =
   # ==============
   # .........................................
   def countTypeCodes(self, afterTime=None, beforeTime=None, public=False):
      """
      @summary: Counts the number of type codes that match the specified 
                   criteria.
      @param afterTime: (optional) Count only type codes modified after this 
                           time.  See time formats in the module documentation.
                           [integer or string]
      @param beforeTime: (optional) Count only type codes modified before this 
                            time.  See time formats in the module 
                            documentation. [integer or string]
      @param public: (optional) If True, use the anonymous client if available
      @return: The number of type codes that match the supplied criteria.
                  [integer]
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("public", int(public))
               ]
      url = "%s/services/sdm/typecodes/" % self.cl.server
      count = self.cl.getCount(url, params)
      return count
   
   # .........................................
   def getTypeCode(self, tcId):
      """
      @summary: Gets a type code object
      @param tcId: The database id of the type code to retrieve [integer]
      @return: A type code object
      """
      url = "%s/services/sdm/typecodes/%s" % (self.cl.server, tcId)
      obj = self.cl.makeRequest(url, method="GET", objectify=True).typecode
      return obj
   
   # .........................................
   def listTypeCodes(self, afterTime=None, beforeTime=None, perPage=100, 
                     page=0, public=False, fullObjects=False):
      """
      @summary: Lists type codes that meet the specified criteria.
      @param afterTime: (optional) Return only type codes modified after this 
                           time.  See time formats in the module documentation. 
                           [integer or string]
      @param beforeTime: (optional) Return only type codes modified before this 
                            time.  See time formats in the module 
                            documentation. [integer or string]
      @param perPage: (optional) Return this many results per page. [integer]
      @param page: (optional) Return this page of results. [integer]
      @param public: (optional) If True, use the anonymous client if available
      @param fullObjects: (optional) If True, return the full objects instead
                             of the list objects
      @return: Type Codes that match the specified parameters. [LmAttObj]
      @note: Returned object has metadata included.  Reference items with 
                "items.item" property
      """
      params = [
                ("afterTime", afterTime),
                ("beforeTime", beforeTime),
                ("page", page),
                ("perPage", perPage),
                ("public", int(public)),
                ("fullObjects", int(fullObjects))
               ]
      url = "%s/services/sdm/typecodes/" % self.cl.server
      items = self.cl.getList(url, parameters=params)
      return items
   
   # .........................................
   def postTypeCode(self, code, title=None, description=None):
      """
      @summary: Posts a new type code to the Lifemapper web services
      @param code: The code to use for this new type code [string]
      @param title: (optional) A title for this type code [string]
      @param description: (optional) An extended description of this type code 
                             [string]
      @return: An objectification of the type code that was newly created
      """
      params = [
                ("code", code),
                ("title", title),
                ("description", description)
               ]
      url = "%s/services/sdm/typecodes" % self.cl.server
      obj = self.cl.makeRequest(url, 
                                method="post", 
                                parameters=params,
                                objectify=True).typecode
      return obj
      
   
   # --------------------------------------------------------------------------

   # .........................................
   def hint(self, query, maxReturned=20):
      """
      @summary: Queries for occurrence sets that match the partial query string
      @param query: The partial string to match (genus species).  Must be at 
                       least 3 characters.
      @param maxReturned: (optional) The maximum number of results to return
      """
      SearchHit = namedtuple('SearchHit', ['name', 'id', 'numPoints'])
      if len(query) < 3:
         raise Exception, "Please provide at least 3 characters to hint service"
      
      params = [
                ("maxReturned", maxReturned)
               ]
      url = "%s/hint/species/%s" % (self.cl.server, query)
      
      res = self.cl.makeRequest(url, method="get", parameters=params)
      
      items = []
      for item in res.split('\n'):
         comps = item.split("\t")
         if len(comps) >= 3:
            items.append(SearchHit(name=comps[0], 
                                id=comps[1], 
                                numPoints=comps[2]))
      return items

   # .........................................
   def getOgcEndpoint(self, obj):
      """
      @summary: Returns the OGC endpoint for a Lifemapper SDM object
      @param obj: The object to get the OGC endpoint of
      @note: This will be moved in version 2.1
      """
      return obj.mapPrefix
   