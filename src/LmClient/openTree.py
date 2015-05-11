"""
@summary: Module containing client functions for interacting with OpenTree web 
             services
@author: CJ Grady / Jeff Cavner
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

"""
from LmClient.localconstants import OTL_HINT_URL, OTL_TREE_WEB_URL

# .............................................................................
class OTLClient(object):
   """
   @summary: Lifemapper interface to Open Tree of Life web services
   """
   # .........................................
   def __init__(self, cl):
      """
      @summary: Constructor
      @param cl: Lifemapper client for connection to web services
      """
      self.cl = cl

   # .........................................
   def getOTLHint(self, taxaName):
      """
      @summary: Calls the Open Tree of Life hint service with a taxa name and 
                   returns matching OTL tree ids
      @param taxaName: The name of the taxa to search for
      """
      url = OTL_HINT_URL
      jsonBody = '{"name":"%s","context_name":"All life"}' % (taxaName)
      res = self.cl.makeRequest(url, 
                                method="POST", 
                                body=jsonBody, 
                                headers={"Content-Type": "application/json"})
      return res
      
   # .........................................
   def getOTLTreeWeb(self, otlTID):
      """
      @summary: Calls the Open Tree of Life tree service with an OTL tree id 
                   and returns a tree in Newick format.
      @param otlTID: Open Tree of Life tree idopen tree tree id
      """
      url = OTL_TREE_WEB_URL
      jsonBody = '{"ott_id":"%s"}' % (otlTID)
      res = self.cl.makeRequest(url, 
                                method="POST", 
                                body=jsonBody, 
                                headers={"Content-Type": "application/json"})
      return res
            