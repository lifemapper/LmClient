"""
@summary: Module containing client functions for interacting with Lifemapper
             Species Distribution Modeling services
@author: CJ Grady
@version: 3.3.0
@status: beta

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
import json
import re

from LmClient.constants import CONTENT_TYPES, LM_INSTANCES_URL
from LmCommon.common.lmconstants import Instances

# .............................................................................
class ParameterOutOfRange(Exception):
   """
   @summary: This exception indicates that an algorithm parameter has an 
                invalid value
   """
   # ...............................
   def __init__(self, param):
      self.param = param
      Exception.__init__(self)
      self.msg = "Parameter %s (%s), min: %s, max: %s, value: %s" % (
                       self.param.displayName, self.param.name, self.param.min, 
                       self.param.max, self.param.value)
   
   # ...............................
   def __repr__(self):
      return "%s %s" % (self.__class__, unicode(self))
      
   # ...............................
   def __str__(self):
      return unicode(self)
   
   # ...............................
   def __unicode__(self):
      return self.msg

# .............................................................................
class ProjectionsNotAllowed(Exception):
   """
   @summary: This exception indicates that projection scenarios are specified, 
                but the value of a parameter indicates that they cannot be
   """
   # ...............................
   def __init__(self, param):
      self.param = param
      Exception.__init__(self)
      self.msg = "Projections specified, but not alowed because the value of %s (%s) does not equal %s" % (
                        self.param.displayName, self.param.value, 
                        self.param.allowProjectionsIfValue)
   
   # ...............................
   def __repr__(self):
      return "%s %s" % (self.__class__, unicode(self))
      
   # ...............................
   def __str__(self):
      return unicode(self)
   
   # ...............................
   def __unicode__(self):
      return self.msg

# .............................................................................
class AlgorithmParameter(object):
   """
   @summary: Algorithm parameter class
   """
   def __init__(self, name, pType, pDefault=None, pMin=None, pMax=None, 
                        pValue=None, doc=None, displayName=None, options=None,
                        allowProjectionsIfValue=None):
      """
      @summary: Constructor
      @param name: The name of the algorithm parameter
      @param pType: The type of the parameter (integer, string, float, etc)
      @param pDefault: (optional) The default value of the parameter
      @param pMin: (optional) The minimum value of the parameter
      @param pMax: (optional) The maximum value of the parameter
      @param pValue: (optional) The value of the parameter
      @param doc: (optional) If this parameter is provided, it is set as the 
                     docstring for the object and the value of the doc attribute
      @param displayName: (optional) A display name for the parameter
      @param options: (optional) A list of (name, value) tuples for the value 
                         options for this parameter
      """
      self.name = name
      self.type = pType
      self.default = pDefault
      self.min = pMin
      self.max = pMax
      self.value = pValue if pValue is not None else self.default
      self.doc = re.sub(' +', ' ', doc.replace('\n', ''))
      self.__doc__ = self.doc
      self.displayName = displayName
      self.options = options
      self.allowProjectionsIfValue = allowProjectionsIfValue
      
# .............................................................................
class Algorithm(object):
   """
   @summary: Algorithm class
   """
   # .........................................
   def __init__(self, clAlg):
      """
      @summary: Constructor
      @param clAlg: Client library algorithm object
      """
      try:
         self.authors = clAlg.authors
      except:
         self.authors = None
         
      try:
         self.description = re.sub(' +', ' ', clAlg.description.replace('\n', ''))
         
      except:
         self.description = None

      try:
         self.link = clAlg.link
      except:
         self.link = None
         
      try:
         self.version = clAlg.version
         self.__version__ = clAlg.version
      except:
         self.version = None
         self.__version__ = None
         
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
             
         try:
            doc = param.doc
         except:
            doc = None
         
         try:
            displayName = param.displayName
         except:
            displayName = None
            
         try:
            options = [(o.name, o.value) for o in param.options]
         except:
            options = None
            
         try:
            allowProj = param.allowProjectionsIfValue
         except:
            allowProj = None
            
            
         p = AlgorithmParameter(param.name, param.type, pDefault=param.default,
                                pMin=pMin, pMax=pMax, doc=doc, 
                                displayName=displayName, options=options,
                                allowProjectionsIfValue=allowProj)
         self.parameters.append(p)
         
   # .........................................
   def getParameter(self, parameterName):
      """
      @summary: Gets the algorithm parameter specified by parameterName
      @param parameterName: The name of the parameter to return
      @rtype: AlgorithmParameter
      """
      for param in self.parameters:
         if param.name.lower() == parameterName.lower():
            return param
      
      # If parameter not found, raise exception
      raise Exception, "Parameter '%s' not found for this algorithm" \
         % parameterName
   
   # .........................................
   def listParameterNames(self):
      """
      @summary: Gets the names of the available parameters for the algorithm
      """
      return [p.name for p in self.parameters]
   
   # .........................................
   def setParameter(self, parameterName, value):
      """
      @summary: Sets the algorithm parameter to the specified value
      @param parameterName: The name of the parameter to set
      @param value: The new value to set the parameter to
      @note: Does not check to make sure the value is valid
      """
      for param in self.parameters:
         if param.name.lower() == parameterName.lower():
            param.value = value
            return
         
      # If parameter not found, raise exception
      raise Exception, "Parameter '%s' not found for this algorithm" \
         % parameterName
   
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
      self.instances = self._getInstances()

   # .........................................
   def _getAlgorithms(self):
      """
      @summary: Gets available Lifemapper SDM algorithms
      @return: Lifemapper algorithms
      """
      #note: This is just done for Pragma and shouldn't be used for regular 
      #         clients
      xmlStr = """\
<?xml version="1.0"?>
<algorithms>
   <algorithm code="ANN" name="Artificial Neural Network" version="0.2">
      <authors>Chopra, Paras, modified by Alex Oshika Avilla and Fabricio Augusto Rodrigues</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/ann.html</link>
      <software>openModeller</software>
      <description>
         An artificial neural network (ANN), also called a simulated neural 
         network (SNN) or commonly just neural network (NN), is an 
         interconnected group of artificial neurons that uses a mathematical or 
         computational model for information processing based on a 
         connectionistic approach to computation. In most cases an ANN is an 
         adaptive system that changes its structure based on external or 
         internal information that flows through the network. In more practical 
         terms, neural networks are non-linear statistical data modeling or 
         decision making tools. They can be used to model complex relationships 
         between inputs and outputs or to find patterns in data. Content 
         retrieved from Wikipedia on the 06th of May, 2008: 
         http://en.wikipedia.org/wiki/Neural_network
      </description>
      <parameters>
         <parameter name="HiddenLayerNeurons" 
                    displayName="Hidden Layer Neurons"
                    min="1" 
                    type="Integer" 
                    default="14">
            <doc>
               Number of neurons in the hidden layer (additional layer to the 
               input and output layers, not connected externally).
            </doc>
         </parameter>
         <parameter name="LearningRate"
                    displayName="Learning Rate" 
                    min="0" 
                    max="1" 
                    type="Float" 
                    default="0.3">
            <doc>
               Learning Rate. Training parameter that controls the size of 
               weight and bias changes during learning.
            </doc>
         </parameter>
         <parameter name="Momentum"
                    displayName="Momentum" 
                    min="0" 
                    max="1" 
                    type="Float" 
                    default="0.05">
            <doc>
               Momentum simply adds a fraction m of the previous weight update 
               to the current one. The momentum parameter is used to prevent 
               the system from converging to a local minimum or saddle point. A 
               high momentum parameter can also help to increase the speed of 
               convergence of the system. However, setting the momentum 
               parameter too high can create a risk of overshooting the 
               minimum, which can cause the system to become unstable. A 
               momentum coefficient that is too low cannot reliably avoid local 
               minima, and can also slow down the training of the system.
            </doc>
         </parameter>
         <parameter name="Choice"
                    displayName="Choice" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               0 = train by epoch, 1 = train by minimum error
            </doc>
            <options>
               <option name="Train by Epoch" value="0" />
               <option name="Train by Minimum Error" value="1" />
            </options>
         </parameter>
         <parameter name="Epoch"
                    displayName="Epoch" 
                    min="1" 
                    type="Integer" 
                    default="5000000">
            <doc>
               Determines when training will stop once the number of iterations 
               exceeds epochs. When training by minimum error, this represents 
               the maximum number of iterations.
            </doc>
         </parameter>
         <parameter name="MinimumError"
                    displayName="Minimum Error" 
                    min="0" 
                    max="0.5" 
                    type="Float" 
                    default="0.01">
            <doc>
               Minimum mean square error of the epoch. Square root of the sum 
               of squared differences between the network targets and actual 
               outputs divided by number of patterns (only for training by 
               minimum error).
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="ATT_MAXENT" name="Maximum Entropy - ATT Implementation" version="3.3.3k">
      <authors>Steven J. Phillips, Miroslav Dudík, Robert E. Schapire</authors>
      <link>https://www.cs.princeton.edu/~schapire/maxent/</link>
      <software>Maxent</software>
      <description>
         A program for maximum entropy modelling of species geographic 
         distributions, written by Steven Phillips, Miro Dudik and Rob 
         Schapire, with support from AT&amp;T Labs-Research, Princeton University, 
         and the Center for Biodiversity and Conservation, American Museum of 
         Natural History.  Thank you to the authors of the following free 
         software packages which we have used here: ptolemy/plot, gui/layouts, 
         gnu/getopt and com/mindprod/ledatastream.
         
         The model for a species is determined from a set of environmental or 
         climate layers (or "coverages") for a set of grid cells in a 
         landscape, together with a set of sample locations where the species 
         has been observed.  The model expresses the suitability of each grid 
         cell as a function of the environmental variables at that grid cell.  
         A high value of the function at a particular grid cell indicates that 
         the grid cell is predicted to have suitable conditions for that 
         species.  The computed model is a probability distribution over all 
         the grid cells.  The distribution chosen is the one that has maximum 
         entropy subject to some constraints: it must have the same expectation 
         for each feature (derived from the environmental layers) as the 
         average over sample locations.
      </description>
      <parameters>
         <parameter name="addallsamplestobackground"
                    displayName="Add All Samples to Background" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Add all samples to the background, even if they have combinations 
               of environmental values that are already present in the 
               background. (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="addsamplestobackground"
                    displayName="Add Samples to Background" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Add to the background any sample for which has a combination of 
               environmental values that isn't already present in the 
               background. (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="adjustsampleradius"
                    displayName="Adjust Sample Radius" 
                    min="0" 
                    type="Integer" 
                    default="0">
            <doc>
               Add this number of pixels to the radius of white/purple dots for 
               samples on pictures of predictions.  Negative values reduce size 
               of dots. 
            </doc>
         </parameter>
         <parameter name="allowpartialdata"
                    displayName="Use Samples with Some Missing Data" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               During model training, allow use of samples that have nodata
               values for one or more environmental variables. (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="appendtoresultsfile"
                    displayName="Append Summary Results to maxentResults File" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               If 0, maxentResults.csv file is reinitialized before each run 
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="applythresholdrule"
                    displayName="Apply Threshold Rule" 
                    min="0" 
                    max="10" 
                    type="Integer" 
                    default="0">
            <doc>
               Apply a threshold rule, generating a binary output grid in 
               addition to the regular prediction grid. (
                 0 : None
                 1 : 'Fixed cumulative value 1',
                 2 : 'Fixed cumulative value 5',
                 3 : 'Fixed cumulative value 10',
                 4 : 'Minimum training presence',
                 5 : '10 percentile training presence',
                 6 : 'Equal training sensitivity and specificity',
                 7 : 'Maximum training sensitivity plus specificity',
                 8 : 'Equal test sensitivity and specificity',
                 9 : 'Maximum test sensitivity plus specificity',
                 10 : 'Equate entropy of thresholded and origial distributions'
               )  
            </doc>
            <options>
               <option name="None" value="0" />
               <option name="Fixed cumulative value 1" value="1" />
               <option name="Fixed cumulative value 5" value="2" />
               <option name="Fixed cumulative value 10" value="3" />
               <option name="Minimum training presence" value="4" />
               <option name="10 percentile training presence" value="5" />
               <option name="Equal training sensitivity and specificity" value="6" />
               <option name="Maximum training sensitivity plus specificity" value="7" />
               <option name="Equal test sensitivity and specificity" value="8" />
               <option name="Maximum test sensitivity plus specificity" value="9" />
               <option name="Equate entropy of thresholded and origial distributions" value="10" />
            </options>
         </parameter>
         <parameter name="autofeature"
                    displayName="Enable Auto Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Automatically select which feature classes to use, based on 
               number of training samples. (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="beta_categorical"
                    displayName="Beta Categorical" 
                    type="Float" 
                    default="-1.0">
            <doc>
               Regularization parameter to be applied to all categorical 
               features; negative value enables automatic setting
            </doc>
         </parameter>
         <parameter name="beta_hinge"
                    displayName="Beta Hinge" 
                    type="Float" 
                    default="-1.0">
            <doc>
               Regularization parameter to be applied to all hinge features;
               negative value enables automatic setting.
            </doc>
         </parameter>
         <parameter name="beta_lqp"
                    displayName="Beta Linear / Quadratic / Product" 
                    type="Float" 
                    default="-1.0">
            <doc>
               Regularization parameter to be applied to all linear, quadratic
               and product features; netagive value enables automatic setting
            </doc>
         </parameter>
         <parameter name="beta_threshold"
                    displayName="Beta Threshold" 
                    type="Float" 
                    default="-1.0">
            <doc>
               Regularization parameter to be applied to all threshold features;
               negative value enables automatic setting
            </doc>
         </parameter>
         <parameter name="betamultiplier"
                    displayName="Beta Multiplier" 
                    min="0" 
                    type="Float" 
                    default="1.0">
            <doc>
               Multiply all automatic regularization parameters by this number.  
               A higher number gives a more spread-out distribution.
            </doc>
         </parameter>
         <parameter name="convergencethreshold"
                    displayName="Convergence Threshold" 
                    min="0" 
                    type="Float" 
                    default="0.00001">
            <doc>
               Stop training when the drop in log loss per iteration drops 
               below this number
            </doc>
         </parameter>
         <parameter name="defaultprevalence"
                    displayName="Default Prevalence" 
                    min="0.0" 
                    max="1.0" 
                    type="Float" 
                    default="0.5">
            <doc>
               Default prevalence of the species: probability of presence at 
               ordinary occurrence points.  See Elith et al., Diversity and 
               Distributions, 2011 for details.
            </doc>
         </parameter>
         <parameter name="doclamp"
                    displayName="Do Clamping" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Apply clamping when projecting (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="extrapolate"
                    displayName="Extrapolate" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Predict to regions of environmental space outside the limits
               encountered during training (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="fadebyclamping"
                    displayName="Fade By Clamping" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Reduce prediction at each point in projections by the difference
               between clamped and non-clamped output at that point (0: no, 
               1:yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="hinge"
                    displayName="Enable Hinge Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Allow hinge features to be used (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="hingethreshold"
                    displayName="Hinge Features Threshold" 
                    min="0" 
                    type="Integer" 
                    default="15">
            <doc>
               Number of samples at which hinge features start being used
            </doc>
         </parameter>
         <parameter name="jackknife"
                    displayName="Do Jackknife to Measure Variable Importance" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Measure importance of each environmental variable by training 
               with each environmental variable first omitted, then used in 
               isolation (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="l2lqthreshold"
                    displayName="Linear to Linear / Quadratic Threshold" 
                    min="0" 
                    type="Integer" 
                    default="10">
            <doc>
               Number of samples at which quadratic features start being used
            </doc>
         </parameter>
         <parameter name="linear"
                    displayName="Enable Linear Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Allow linear features to be used (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="logscale"
                    displayName="Logscale Raw / Cumulative Pictures" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               If selected, all pictures of models will use a logarithmic scale 
               for color-coding (0: no, 1: yes))
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="lq2lqptthreshold"
                    displayName="Linear / Quadratic to Linear / Quadratic / Product / Threshold Features Threshold" 
                    min="0" 
                    type="Integer" 
                    default="80">
            <doc>
               Number of samples at which product and threshold features start
               being used
            </doc>
         </parameter>
         <parameter name="maximumbackground"
                    displayName="Maximum Number of Background Points" 
                    min="0" 
                    type="Integer" 
                    default="10000">
            <doc>
               If this number of background points / grid cells is larger than 
               this number, then this number of cells is chosen randomly for 
               background points points
            </doc>
         </parameter>
         <parameter name="maximumiterations"
                    displayName="Maximum Number of Training Iterations" 
                    min="0" 
                    type="Integer" 
                    default="500">
            <doc>
               Stop training after this many iterations of the optimization 
               algorithm
            </doc>
         </parameter>
         <parameter name="outputformat" 
                    displayName="Output Format" 
                    min="0" 
                    max="2" 
                    type="Integer" 
                    default="1">
            <doc>
               Representation of probabilities used in writing output grids.  
               (0: raw, 1: logistic, 2: cumulative)
            </doc>
            <options>
               <option name="Raw" value="0" />
               <option name="Logistic" value="1" />
               <option name="Cumulative" value="2" />
            </options>
         </parameter>
         <parameter name="outputgrids"
                    displayName="Write Output Grids" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Write output grids.  Turning this off when doing replicate runs 
               causes only the summary grids (average, std deviation, etc.) to 
               be written, not those for the individual runs. (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="perspeciesresults"
                    displayName="Per Species Results" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Write separate maxentResults file for each species (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="pictures"
                    displayName="Generate Pictures" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Create a .png image for each output grid (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="plots"
                    displayName="Generate Plots" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Write various plots for inclusion in .html output (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="product"
                    displayName="Enable Product Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Allow product features to be used (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="quadratic"
                    displayName="Enable Quadratic Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Allow quadtratic features to be used (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="randomseed"
                    displayName="Random Seed" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               If selected, a different random seed will be used for each run, 
               so a different random test / train partition (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="randomtestpoints"
                    displayName="Random Test Points Percentage" 
                    min="0" 
                    max="100" 
                    type="Integer" 
                    default="0">
            <doc>
               Percentage of presence localities to be randomly set aside as
               test poits, used to compute AUC, omission, etc.
            </doc>
         </parameter>
         <parameter name="replicates"
                    displayName="Number of Replicates" 
                    min="1" 
                    type="Integer" 
                    default="1"
                    allowProjectionsIfValue="1">
            <doc>
               Number of replicate runs to do when cross-validating, 
               boostrapping or doing sampling with replacement runs.  If this 
               number is greater than 1, future projection will be disabled as
               multiple ruleset lambdas files will be generated.
            </doc>
         </parameter>
         <parameter name="replicatetype"
                    displayName="Replicate Type" 
                    min="0" 
                    max="2" 
                    type="Integer" 
                    default="0">
            <doc>
               If replicates > 1, do multiple runs of this type.  Crossvalidate: 
               samples divided into replicates folds; each fold in turn used 
               for test data.  Bootstrap: replicate sample sets chosen by 
               sampling with replacement.  Subsample: replicate sample sets 
               chosen by removing random test percentage without replacement to 
               be used for evaluation. (0: Crossvalidate, 1: Bootstrap, 2: 
               Subsample)
            </doc>
            <options>
               <option name="Cross-validate" value="0" />
               <option name="Bootstrap" value="1" />
               <option name="Subsample" value="2" />
            </options>
         </parameter>
         <parameter name="removeduplicates"
                    displayName="Remove Duplicates" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Remove duplicate presence records.  If environmental data are in 
               grids, duplicates are records in the same grid cell.  Otherwise, 
               duplicates are records with identical coordinates. (0: no, 
               1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="responsecurves"
                    displayName="Generate Response Curves" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Create graphs showing how predicted relative probability of 
               occurrence depends on the value of each environmental variable.
               (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="responsecurvesexponent"
                    displayName="Response Curves Exponent" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Instead of showing the logistic value for the y axis in response
               curves, show the exponent (a linear combination of features)
               (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="threshold"
                    displayName="Enable Threshold Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Allow threshold features to be used (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="verbose"
                    displayName="Produce Verbose Output" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Give detailed diagnostics for debugging (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="writebackgroundpredictions"
                    displayName="Write Background Predictions" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Write .csv file with predictions at background points 
               (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="writeclampgrid"
                    displayName="Write Clamp Grid" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Write a grid that shows the spatial distribution of clamping.  
               At each point, the value is the absolute difference between 
               prediction values with and without clamping. (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="writemess"
                    displayName="Do MESS Analysis When Projecting" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               A multidimensional environmental similarity surface (MESS) shows 
               where novel climate conditions exist in the projection layers.  
               The analysis shows botht he degree of novelness and the variable 
               that is most out of range. (0: no, 1: yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="writeplotdata"
                    displayName="Write Plot Data" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Write output files containing the data used to make response 
               curves, for import into external plotting software
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="BIOCLIM" name="Bioclim" version="0.2">
      <authors>Nix, H. A.</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/bioclim.html</link>
      <software>openModeller</software>
      <description>
         Implements the Bioclimatic Envelope Algorithm. For each given 
         environmental variable the algorithm finds the mean and standard 
         deviation (assuming normal distribution) associated to the occurrence 
         points. Each variable has its own envelope represented by the interval 
         [m - c*s, m + c*s], where 'm' is the mean; 'c' is the cutoff input 
         parameter; and 's' is the standard deviation. Besides the envelope, 
         each environmental variable has additional upper and lower limits 
         taken from the maximum and minimum values related to the set of 
         occurrence points. In this model, any point can be classified as: 
         Suitable: if all associated environmental values fall within the 
         calculated envelopes; Marginal: if one or more associated 
         environmental value falls outside the calculated envelope, but still 
         within the upper and lower limits. Unsuitable: if one or more 
         associated enviromental value falls outside the upper and lower 
         limits. Bioclim's categorical output is mapped to probabilities of 
         1.0, 0.5 and 0.0 respectively.
      </description>
      <parameters>
         <parameter name="StandardDeviationCutoff"
                    displayName="Standard Deviation Cutoff" 
                    min="0.0" 
                    type="Float" 
                    default="0.674">
            <doc>
               Standard deviation cutoff for all bioclimatic envelopes. 
               Examples of (fraction of inclusion, parameter value) are: 
               (50.0%, 0.674); (68.3%, 1.000); (90.0%, 1.645); (95.0%, 1.960); 
               (99.7%, 3.000)
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="CSMBS" name="Climate Space Model" version="0.4">
      <authors>Neil Caithness</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/csmbs.html</link>
      <software>openModeller</software>
      <description>
         Climate Space Model [CSM] is a principle components based algorithm 
         developed by Dr. Neil Caithness. The component selection process in 
         this algorithm implementation is based on the Broken-Stick cutoff 
         where any component with an eigenvalue less than (n stddevs above a 
         randomised sample) is discarded. The original CSM was written as 
         series of Matlab functions.
      </description>
      <parameters>
         <parameter name="Randomisations"
                    displayName="Number of Randomizations" 
                    min="1" 
                    max="1000" 
                    type="Integer" 
                    default="8">
            <doc>
               The Broken Stick method of selecting the number of components to 
               keep is carried out by randomising the row order of each column 
               in the environmental matrix and then obtaining the eigen value 
               for the randomised matrix. This is repeatedly carried out for 
               the amount of times specified by the user here.
            </doc>
         </parameter>
         <parameter name="StandardDeviations"
                    displayName="Stnadard Deviations" 
                    min="-10" 
                    max="10" 
                    type="Float" 
                    default="2.0">
            <doc>
               When all the eigen values for the 'shuffled' environmental 
               matrix have been summed this number of standard deviations is 
               added to the mean of the eigen values. Any components whose 
               eigen values are above this threshold are retained.
            </doc>
         </parameter>
         <parameter name="MinComponents"
                    displayName="Minimum Number of Components" 
                    min="1" 
                    max="20" 
                    type="Integer" 
                    default="1">
            <doc>
               If not enough components are selected, the model produced will 
               be erroneous or fail. Usually three or more components are 
               acceptable
            </doc>
         </parameter>
         <parameter name="VerboseDebugging"
                    displayName="Enable Verbose Debugging" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               Set this to 1 to show extremely verbose diagnostics. Set this to 
               0 to disable verbose diagnostics
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="DG_GARP" name="GARP - DesktopGARP implementation" version="1.1 alpha">
      <authors>Stockwell, D. R. B., modified by Ricardo Scachetti Pereira</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/dg_garp.html</link>
      <software>openModeller</software>
      <description>
         GARP is a genetic algorithm that creates ecological niche models for 
         species. The models describe environmental conditions under which the 
         species should be able to maintain populations. For input, GARP uses a 
         set of point localities where the species is known to occur and a set 
         of geographic layers representing the environmental parameters that 
         might limit the species' capabilities to survive.
      </description>
      <parameters>
         <parameter name="MaxGenerations"
                    displayName="Maximum Number of Generations" 
                    min="1" 
                    type="Integer" 
                    default="400">
            <doc>
               Maximum number of iterations (generations) run by the Genetic 
               Algorithm
            </doc>
         </parameter>
         <parameter name="ConvergenceLimit"
                    displayName="Convergence Limit" 
                    min="0" 
                    max="1" 
                    type="Float" 
                    default="0.01">
            <doc>
               Defines the convergence value that makes the algorithm stop 
               (before reaching MaxGenerations).
            </doc>
         </parameter>
         <parameter name="PopulationSize"
                    displayName="Population Size" 
                    min="1" 
                    max="500" 
                    type="Integer" 
                    default="50">
            <doc>
               Maximum number of rules to be kept in solution.
            </doc>
         </parameter>
         <parameter name="Resamples"
                    displayName="Number of Resamples" 
                    min="1" 
                    max="100000" 
                    type="Integer" 
                    default="2500">
            <doc>
               Number of points sampled (with replacement) used to test rules.
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="DG_GARP_BS" name="GARP with Best Subsets - DesktopGARP implementation" version="3.0.2">
      <authors>Anderson, R. P., D. Lew, D. and A. T. Peterson.</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/dg_garp_bs.html</link>
      <software>openModeller</software>
      <description>
         GARP is a genetic algorithm that creates ecological niche models for 
         species. The models describe environmental conditions under which the 
         species should be able to maintain populations. For input, GARP uses a 
         set of point localities where the species is known to occur and a set 
         of geographic layers representing the environmental parameters that 
         might limit the species' capabilities to survive.
      </description>
      <parameters>
         <parameter name="TrainingProportion"
                    displayName="Training Proportion" 
                    min="0" 
                    max="100" 
                    type="Float" 
                    default="50">
            <doc>
               Percentage of occurrence data to be used to train models.
            </doc>
         </parameter>
         <parameter name="TotalRuns"
                    displayName="Total Number of Runs" 
                    min="0" 
                    max="10000" 
                    type="Integer" 
                    default="20">
            <doc>
               Maximum number of GARP runs to be performed.
            </doc>
         </parameter>
         <parameter name="HardOmissionThreshold"
                    displayName="Hard Omission Threshold" 
                    min="0" 
                    max="100" 
                    type="Float" 
                    default="100">
            <doc>
               Maximum acceptable omission error. Set to 100% to use only soft 
               omission.
            </doc>
         </parameter>
         <parameter name="ModelsUnderOmissionThreshold"
                    displayName="Models Under Omission Threshold" 
                    min="0" 
                    max="10000" 
                    type="Integer" 
                    default="20">
            <doc>
               Minimum number of models below omission threshold.
            </doc>
         </parameter>
         <parameter name="CommissionThreshold"
                    displayName="Commission Threshold" 
                    min="0" 
                    max="100" 
                    type="Float" 
                    default="50">
            <doc>
               Percentage of distribution models to be taken regarding 
               commission error.
            </doc>
         </parameter>
         <parameter name="CommissionSampleSize"
                    displayName="Commission Sample Size" 
                    min="1" 
                    type="Integer" 
                    default="10000">
            <doc>
               Number of samples used to calculate commission error.
            </doc>
         </parameter>
         <parameter name="MaxThreads"
                    displayName="Maximum Number of Threads" 
                    min="1" 
                    max="1024" 
                    type="Integer" 
                    default="1">
            <doc>
               Maximum number of threads of executions to run simultaneously.
            </doc>
         </parameter>
         <parameter name="MaxGenerations"
                    displayName="Maximum Number of Generations" 
                    min="1" 
                    type="Integer" 
                    default="400">
            <doc>
               Maximum number of iterations (generations) run by the Genetic 
               Algorithm.
            </doc>
         </parameter>
         <parameter name="ConvergenceLimit"
                    displayName="Convergence Limit" 
                    min="0" 
                    max="1" 
                    type="Float" 
                    default="0.01">
            <doc>
               Defines the convergence value that makes the algorithm stop 
               (before reaching MaxGenerations).
            </doc>
         </parameter>
         <parameter name="PopulationSize"
                    displayName="Population Size" 
                    min="1" 
                    max="500" 
                    type="Integer" 
                    default="50">
            <doc>
               Maximum number of rules to be kept in solution.
            </doc>
         </parameter>
         <parameter name="Resamples"
                    displayName="Number of Resamples" 
                    min="1" 
                    max="100000" 
                    type="Integer" 
                    default="2500">
            <doc>
               Number of points sampled (with replacement) used to test rules.
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="ENVDIST" name="Environmental Distance" version="0.5">
      <authors>Mauro E. S. Munoz, Renato De Giovanni, Danilo J. S. Bellini</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/envdist.html</link>
      <software>openModeller</software>
      <description>
         Generic algorithm based on environmental dissimilarity metrics. When 
         used with the Gower metric and maximum distance 1, this algorithm 
         should produce the same result of the algorithm known as DOMAIN.
      </description>
      <parameters>
         <parameter name="DistanceType"
                    displayName="Distance Type" 
                    min="1" 
                    max="4" 
                    type="Integer" 
                    default="1">
            <doc>
               Metric used to calculate distances: 1=Euclidean, 2=Mahalanobis, 
               3=Manhattan/Gower, 4=Chebyshev
            </doc>
            <options>
               <option name="Euclidean" value="1" />
               <option name="Mahalanobis" value="2" />
               <option name="Manhattan / Gower" value="3" />
               <option name="Chebyshev" value="4" />
            </options>
         </parameter>
         <parameter name="NearestPoints"
                    displayName="Nearest N Points" 
                    min="0" 
                    max="1000" 
                    type="Integer" 
                    default="1">
            <doc>
               Nearest 'n' points whose mean value will be the reference when 
               calculating environmental distances. When set to 1, distances 
               will be measured to the closest point, which is the same 
               behavior of the previously existing minimum distance algorithm. 
               When set to 0, distances will be measured to the average of all 
               presence points, which is the same behavior of the previously 
               existing distance to average algorithm. Intermediate values 
               between 1 and the total number of presence points are now 
               accepted.
            </doc>
         </parameter>
         <parameter name="MaxDistance"
                    displayName="Maximum Environmental Distance" 
                    min="0" 
                    max="1" 
                    type="Float" 
                    default="0.1">
            <doc>
               Maximum distance to the reference in the environmental space, 
               above which the conditions will be considered unsuitable for 
               presence. Since 1 corresponds to the biggest possible distance 
               between any two points in the environment space, setting the 
               maximum distance to this value means that all points in the 
               environmental space will have an associated probability. The 
               probability of presence for points that fall within the range of 
               the maximum distance is inversely proportional to the distance 
               to the reference point (linear decay). The only exception is 
               when the maximum distance is 1 and the metric is Mahalanobis, 
               which will produce probabilities following the chi-square 
               distribution.
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="GARP" name="GARP" version="3.3">
      <authors> Stockwell, D. R. B., modified by Ricardo Scachetti Pereira</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/garp.html</link>
      <software>openModeller</software>
      <description>
         GARP is a genetic algorithm that creates ecological niche models for 
         species. The models describe environmental conditions under which the 
         species should be able to maintain populations. For input, GARP uses a 
         set of point localities where the species is known to occur and a set 
         of geographic layers representing the environmental parameters that 
         might limit the species' capabilities to survive. This implementation 
         is a complete rewrite of the DesktopGarp code, and it also contains 
         the following changes/improvements: (1) Gene values changed from 
         integers (between 1 and 253) to floating point numbers (between -1.0 
         and 1.0). This avoids precision problems in environment values during 
         projection (for example, if an environment variable has the value 2.56 
         in some raster cell and 2.76 in another one, DesktopGarp rounds them 
         off to 3). (2) Atomic rules were removed since they seem to have 
         little significance compared to the other rules. (3) Heuristic 
         operator parameters (percentage of mutation and crossover per 
         iteration) are now static since they used to converge to fixed values 
         during the very first iterations. This implementation simply keeps the 
         converged values. (4) A bug was fixed in the procedure responsible for 
         ordering the rules. When a rule was only replacing another, it was 
         being included in the wrong position.
      </description>
      <parameters>
         <parameter name="MaxGenerations"
                    displayName="Maximum Number of Generations" 
                    min="1" 
                    type="Integer" 
                    default="400">
            <doc>
               Maximum number of iterations (generations) run by the Genetic 
               Algorithm.
            </doc>
         </parameter>
         <parameter name="ConvergenceLimit"
                    displayName="Convergence Limit" 
                    min="0" 
                    max="1" 
                    type="Float" 
                    default="0.01">
            <doc>
               Defines the convergence value that makes the algorithm stop 
               (before reaching MaxGenerations).
            </doc>
         </parameter>
         <parameter name="PopulationSize"
                    displayName="Population Size" 
                    min="1" 
                    max="500" 
                    type="Integer" 
                    default="50">
            <doc>
               Maximum number of rules to be kept in solution.
            </doc>
         </parameter>
         <parameter name="Resamples"
                    displayName="Number of Resamples" 
                    min="1" 
                    max="100000" 
                    type="Integer" 
                    default="2500">
            <doc>
               Number of points sampled (with replacement) used to test rules.
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="GARP_BS" name="GARP with Best Subsets" version="3.0.4">
      <authors>Anderson, R. P., D. Lew, D. and A. T. Peterson.</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/garp_bs.html</link>
      <software>openModeller</software>
      <description>
         GARP is a genetic algorithm that creates ecological niche models for 
         species. The models describe environmental conditions under which the 
         species should be able to maintain populations. For input, GARP uses a 
         set of point localities where the species is known to occur and a set 
         of geographic layers representing the environmental parameters that 
         might limit the species' capabilities to survive. This algorithm 
         applies the Best Subsets procedure using the new openModeller 
         implementation in each GARP run. Please refer to GARP single run 
         algorithm description for more information about the differences 
         between DesktopGarp and the new GARP implementation.
      </description>
      <parameters>
         <parameter name="TrainingProportion"
                    displayName="Training Proportion" 
                    min="0" 
                    max="100" 
                    type="Float" 
                    default="50">
            <doc>
               Percentage of occurrence data to be used to train models.
            </doc>
         </parameter>
         <parameter name="TotalRuns"
                    displayName="Total Number of Runs" 
                    min="0" 
                    max="10000" 
                    type="Integer" 
                    default="20">
            <doc>
               Maximum number of GARP runs to be performed.
            </doc>
         </parameter>
         <parameter name="HardOmissionThreshold"
                    displayName="Hard Omission Threshold" 
                    min="0" 
                    max="100" 
                    type="Float" 
                    default="100">
            <doc>
               Maximum acceptable omission error. Set to 100% to use only soft 
               omission.
            </doc>
         </parameter>
         <parameter name="ModelsUnderOmissionThreshold"
                    displayName="Models Under Omission Threshold" 
                    min="0" 
                    max="10000" 
                    type="Integer" 
                    default="20">
            <doc>
               Minimum number of models below omission threshold.
            </doc>
         </parameter>
         <parameter name="CommissionThreshold"
                    displayName="Commission Threshold" 
                    min="0" 
                    max="100" 
                    type="Float" 
                    default="50">
            <doc>
               Percentage of distribution of models to be taken regarding 
               commission error.
            </doc>
         </parameter>
         <parameter name="CommissionSampleSize"
                    displayName="Commission Sample Size" 
                    min="1" 
                    type="Integer" 
                    default="10000">
            <doc>
               Number of samples used to calculate commission error.
            </doc>
         </parameter>
         <parameter name="MaxThreads"
                    displayName="Maximum Number of Threads" 
                    min="1" 
                    max="1024" 
                    type="Integer" 
                    default="1">
            <doc>
               Maximum number of threads of executions to run simultaneously.
            </doc>
         </parameter>
         <parameter name="MaxGenerations"
                    displayName="Maximum Number of Generations" 
                    min="1" 
                    type="Integer" 
                    default="400">
            <doc>
               Maximum number of iterations (generations) run by the Genetic 
               Algorithm.
            </doc>
         </parameter>
         <parameter name="ConvergenceLimit"
                    displayName="Convergence Limit" 
                    min="0" 
                    max="1" 
                    type="Float" 
                    default="0.01">
            <doc>
               Defines the convergence value that makes the algorithm stop 
               (before reaching MaxGenerations).
            </doc>
         </parameter>
         <parameter name="PopulationSize"
                    displayName="Population Size" 
                    min="1" 
                    max="500" 
                    type="Integer" 
                    default="50">
            <doc>
               Maximum number of rules to be kept in solution.
            </doc>
         </parameter>
         <parameter name="Resamples"
                    displayName="Number of Resamples" 
                    min="1" 
                    max="100000" 
                    type="Integer" 
                    default="2500">
            <doc>
               Number of points sampled (with replacement) used to test rules.
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="MAXENT" name="Maximum Entropy - openModeller Implementation" version="1.0">
      <authors>Steven J. Phillips, Miroslav Dudík, Robert E. Schapire</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/maxent.html</link>
      <software>openModeller</software>
      <description>
         The principle of maximum entropy is a method for analyzing available 
         qualitative information in order to determine a unique epistemic 
         probability distribution. It states that the least biased distribution 
         that encodes certain given information is that which maximizes the 
         information entropy (content retrieved from Wikipedia on the 19th of 
         May, 2008: http://en.wikipedia.org/wiki/Maximum_entropy). This 
         implementation in openModeller follows the same approach of Maxent 
         (Phillips et al. 2004). It was compared with Maxent 3.3.3e through a 
         standard experiment using all possible combinations of parameters, 
         generating models with the same number of iterations, at least a 90% 
         rate of matching best features considering all iterations, 
         distribution maps with a correlation (r) greater than 0.999 and no 
         difference in the final loss. However, previous implementations of 
         this algorithm (before version 1.0) used to generate quite different 
         results. The first versions were based on an existing third-party 
         Maximum Entropy library which produced low quality models compared 
         with all other algorithms. After that, the algorithm was re-written a 
         couple of times by Elisangela Rodrigues as part of her Doctorate. 
         Finally, the EUBrazil-OpenBio project funded the remaining work to 
         make this algorithm compatible with Maxent. Please note that not all 
         functionality available from Maxent is available here - in particular 
         the possibility of using collecting bias and categorical maps is not 
         present, as well as many specific parameters for advanced users. 
         However, you should be able to get compatible results for all other 
         available parameters.
      </description>
      <parameters>
         <parameter name="NumberOfBackgroundPoints"
                    displayName="Number of Background Points" 
                    min="0" 
                    max="10000" 
                    type="Integer" 
                    default="10000">
            <doc>
               Number of background points to be generated.
            </doc>
         </parameter>
         <parameter name="UseAbsencesAsBackground"
                    displayName="Use Absences As Background" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="0">
            <doc>
               When absence points are provided, this parameter can be used to 
               instruct the algorithm to use them as background points. This 
               would prevent the algorithm to randomly generate them, also 
               facilitating comparisons between different algorithms.
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="IncludePresencePointsInBackground"
                    displayName="Include Presence Points In Background" 
                    min="0" 
                    max="1"
                    type="Integer" 
                    default="1">
            <doc>
               Include input points in the background: 0=No, 1=Yes.
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="NumberOfIterations"
                    displayName="Number of Iterations" 
                    min="1" 
                    type="Integer" 
                    default="500">
            <doc>
               Number of iterations.
            </doc>
         </parameter>
         <parameter name="TerminateTolerance"
                    displayName="Terminate Tolerance" 
                    min="0" 
                    type="Float" 
                    default="0.00001">
            <doc>
               Tolerance for detecting model convergence.
            </doc>
         </parameter>
         <parameter name="OutputFormat"
                    displayName="Output Format" 
                    min="1" 
                    max="2" 
                    type="Integer" 
                    default="2">
            <doc>
               Output format: 1 = Raw, 2 = Logistic. 
            </doc>
            <options>
               <option name="Raw" value="1" />
               <option name="Logistic" value="2" />
            </options>
         </parameter>
         <parameter name="QuadraticFeatures"
                    displayName="Enable Quadratic Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Enable quadratic features (0=no, 1=yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="ProductFeatures"
                    displayName="Enable Product Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Enable product features (0=no, 1=yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="HingeFeatures"
                    displayName="Enable Hinge Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Enable hinge features (0=no, 1=yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="ThresholdFeatures"
                    displayName="Enable Threshold Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Enable threshold features (0=no, 1=yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="AutoFeatures"
                    displayName="Enable Auto Features" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Enable auto features (0=no, 1=yes)
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="MinSamplesForProductThreshold"
                    displayName="Minimum Samples For Product and Threshold Features" 
                    min="1" 
                    type="Integer" 
                    default="80">
            <doc>
               Number of samples at which product and threshold features start 
               being used (only when auto features is enabled).
            </doc>
         </parameter>
         <parameter name="MinSamplesForQuadratic"
                    displayName="Minimum Number of Samples for Quadratic Features" 
                    min="1" 
                    type="Integer" 
                    default="10">
            <doc>
               Number of samples at which quadratic features start being used 
               (only when auto features is enabled).
            </doc>
         </parameter>
         <parameter name="MinSamplesForHinge"
                    displayName="Minimum Number of Samples For Hinge Features" 
                    min="1" 
                    type="Integer" 
                    default="15">
            <doc>
               Number of samples at which hinge features start being used (only 
               when auto features is enabled).
            </doc>
         </parameter>
      </parameters>
   </algorithm>
   <algorithm code="SVM" name="Support Vector Machines" version="0.5">
      <authors>Vladimir N. Vapnik</authors>
      <link>http://openmodeller.sourceforge.net/algorithms/svm.html</link>
      <software>openModeller</software>
      <description>
         Support vector machines map input vectors to a higher dimensional 
         space where a maximal separating hyperplane is constructed. Two 
         parallel hyperplanes are constructed on each side of the hyperplane 
         that separates the data. The separating hyperplane is the hyperplane 
         that maximises the distance between the two parallel hyperplanes. An 
         assumption is made that the larger the margin or distance between 
         these parallel hyperplanes the better the generalisation error of the 
         classifier will be. The model produced by support vector 
         classification only depends on a subset of the training data, because 
         the cost function for building the model does not care about training 
         points that lie beyond the margin. Content retrieved from Wikipedia on 
         the 13th of June, 2007: 
         http://en.wikipedia.org/w/index.php?title=Support_vector_machine&amp;oldid=136646498. 
         The openModeller implementation of SVMs makes use of the libsvm 
         library version 2.85: Chih-Chung Chang and Chih-Jen Lin, LIBSVM: a 
         library for support vector machines, 2001. Software available at 
         http://www.csie.ntu.edu.tw/~cjlin/libsvm. Release history: 
         version 0.1: initial release version 0.2: New parameter to specify the 
         number of pseudo-absences to be generated; upgraded to libsvm 2.85; 
         fixed memory leaks version 0.3: when absences are needed and the 
         number of pseudo absences to be generated is zero, it will default to 
         the same number of presences version 0.4: included missing 
         serialization of C version 0.5: the indication if the algorithm needed 
         normalized environmental data was not working when the algorithm was 
         loaded from an existing model.
      </description>
      <parameters>
         <parameter name="SvmType"
                    displayName="SVM Type" 
                    min="0" 
                    max="2" 
                    type="Integer" 
                    default="0">
            <doc>
               Type of SVM: 0 = C-SVC, 1 = Nu-SVC, 2 = one-class SVM
            </doc>
            <options>
               <option name="C-SVC" value="0" />
               <option name="Nu-SVC" value="1" />
               <option name="One-class SVM" value="2" />
            </options>
         </parameter>
         <parameter name="KernelType"
                    displayName="Kernel Type" 
                    min="0" 
                    max="4" 
                    type="Integer" 
                    default="2">
            <doc>
               Type of kernel function: 0 = linear: u'*v , 1 = polynomial: 
               (gamma*u'*v + coef0)^degree , 2 = radial basis function: 
               exp(-gamma*|u-v|^2)
            </doc>
            <options>
               <option name="Linear: u'*v" value="0" />
               <option name="Polynomial: (gamma*u'*v + coef0) ^ degree" value="1" />
               <option name="Radial basis function: exp(-gamma*|u-v|^2)" value="2" />
            </options>
         </parameter>
         <parameter name="Degree"
                    displayName="Polynomial Kernel Degree" 
                    min="0" 
                    type="Integer" 
                    default="3">
            <doc>
               Degree in kernel function (only for polynomial kernels).
            </doc>
         </parameter>
         <parameter name="Gamma"
                    displayName="Kernel Gamma" 
                    type="Float" 
                    default="0">
            <doc>
               Gamma in kernel function (only for polynomial and radial basis 
               kernels). When set to zero, the default value will actually be 
               1/k, where k is the number of layers.
            </doc>
         </parameter>
         <parameter name="Coef0"
                    displayName="Polynomial Kernel Coef0" 
                    type="Float" 
                    default="0">
            <doc>
               Coef0 in kernel function (only for polynomial kernels).
            </doc>
         </parameter>
         <parameter name="C"
                    displayName="Cost" 
                    min="0" 
                    type="Float" 
                    default="1">
            <doc>
               Cost (only for C-SVC types).
            </doc>
         </parameter>
         <parameter name="Nu"
                    displayName="Nu" 
                    min="0.001" 
                    max="1" 
                    type="Float" 
                    default="0.5">
            <doc>
               Nu (only for Nu-SVC and one-class SVM).
            </doc>
         </parameter>
         <parameter name="ProbabilisticOutput"
                    displayName="Generate Probabilistic Output" 
                    min="0" 
                    max="1" 
                    type="Integer" 
                    default="1">
            <doc>
               Indicates if the output should be a probability instead of a 
               binary response (only available for C-SVC and Nu-SVC).
            </doc>
            <options>
               <option name="No" value="0" />
               <option name="Yes" value="1" />
            </options>
         </parameter>
         <parameter name="NumberOfPseudoAbsences"
                    displayName="Number of Pseudo Absences" 
                    min="0" 
                    type="Integer" 
                    default="0">
            <doc>
               Number of pseudo-absences to be generated (only for C-SVC and 
               Nu-SVC when no absences have been provided). When absences are 
               needed, a zero parameter will default to the same number of 
               presences.
            </doc>
         </parameter>
      </parameters>
   </algorithm>   
</algorithms>
"""
      obj = self.cl.objectify(xmlStr)
      #url = "%s/clients/algorithms.xml" % self.cl.server
      #obj = self.cl.makeRequest(url, method="GET", objectify=True)
      return obj
   
   # .........................................
   def _getInstances(self):
      """
      @summary: Gets the available instances for query from the Lifemapper 
                   server
      """
      #note: This is just done for Pragma and shouldn't be used for regular 
      #         clients
      xmlStr = """\
<?xml version="1.0"?>
<instances>
</instances>
"""
      obj = self.cl.objectify(xmlStr)
      #obj = self.cl.makeRequest(LM_INSTANCES_URL, method="GET", objectify=True)
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
         raise Exception("Algorithm code: %s was not recognized" % code)
      return a
   
   # .........................................
   def getAvailableInstances(self):
      """
      @summary: Returns a list of (name, base service url) tuples of available 
                   instances to be queried by the client
      """
      availableInstances = []
      
      myVersion = self.cl.getVersionNumbers()
      
      for instance in self.instances:
         minVersion = self.cl.getVersionNumbers(verStr=instance.minimumClientVersion)
         maxVersion = self.cl.getVersionNumbers(verStr=instance.maximumClientVersion)
         
         if myVersion >= minVersion and myVersion <= maxVersion:
            availableInstances.append((instance.name, instance.baseUrl))
      
      return availableInstances
   
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
   def deleteExperiment(self, expId):
      """
      @summary: Deletes a Lifemapper SDM experiment
      @param expId: The id of the experiment to be deleted. [integer]
      """
      url = "%s/services/sdm/experiments/%s" % (self.cl.server, expId)
      obj = self.cl.makeRequest(url, method="DELETE", objectify=True)
      return obj
    
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
   def getExperimentPackage(self, expId, filename):
      """
      @summary: Gets the package of output for a Lifemapper SDM experiment
      @param expId: The id of the experiment to be returned. [integer]
      @return: True if the write was successful
      """
      url = "%s/services/sdm/experiments/%s/package" % (self.cl.server, expId)
      cnt = self.cl.makeRequest(url, method="GET")
      f = open(filename, 'wb')
      f.write(cnt)
      f.close()
      return True
       
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
      
      # Validate algorithm parameters
      self.validateAlgorithmParameters(algorithmParameters, prjScns)

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
   def deleteLayer(self, lyrId):
      """
      @summary: Deletes a Lifemapper environmental layer
      @param lyrId: The id of the layer to be deleted. [integer]
      """
      url = "%s/services/sdm/layers/%s" % (self.cl.server, lyrId)
      obj = self.cl.makeRequest(url, method="DELETE", objectify=True)
      return obj

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
         f = open(filename, 'wb')
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
         body = open(fileName, 'rb').read()
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
   def deleteOccurrenceSet(self, occId):
      """
      @summary: Deletes a Lifemapper occurrence set
      @param occId: The id of the occurrence set to be deleted. [integer]
      """
      url = "%s/services/sdm/occurrences/%s" % (self.cl.server, occId)
      obj = self.cl.makeRequest(url, method="DELETE", objectify=True)
      return obj
   
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
   def getOccurrenceSetShapefile(self, occId, filename=None, overwrite=False):
      """
      @summary: Gets a Lifemapper occurrence set as a shapefile
      @param occId: The id of the occurrence set to get. [integer]
      @param filename: (optional) The name of the file location to save the 
                          output. [string]  If it is not provided the content 
                          will be returned as a string.  If the filename is a 
                          .zip file, the output will be written to that file.  
                          If it is a .shp path, the output will use that base
                          name for output.  If the filename is a directory, the
                          files will be written to that directory with the 
                          names in the zipfile.
      @param overwrite: (optional): Should files be overwritten if they exist?
      @note: This function will be removed in a later version in favor of 
                specifying the format when making the get request
      """
      url = "%s/services/sdm/occurrences/%s/shapefile" % (self.cl.server, occId)
      cnt = self.cl.makeRequest(url, method="GET")
      if filename is not None:
         self.cl.autoUnzipShapefile(cnt, filename, overwrite=overwrite)
         #f = open(filename, 'wb')
         #f.write(cnt)
         #f.close()
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
            postBody = open(fileName, 'rb').read()
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
   def deleteProjection(self, prjId):
      """
      @summary: Deletes a Lifemapper SDM projection
      @param prjId: The id of the projection to be deleted. [integer]
      """
      url = "%s/services/sdm/projections/%s" % (self.cl.server, prjId)
      obj = self.cl.makeRequest(url, method="DELETE", objectify=True)
      return obj
    
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
         f = open(filename, 'wb')
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
   def deleteScenario(self, scnId):
      """
      @summary: Deletes a Lifemapper scenario
      @param scnId: The id of the scenario to be deleted. [integer]
      """
      url = "%s/services/sdm/scenarios/%s" % (self.cl.server, scnId)
      obj = self.cl.makeRequest(url, method="DELETE", objectify=True)
      return obj
   
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
   def deleteTypeCode(self, tcId):
      """
      @summary: Deletes a Lifemapper SDM type code
      @param tcId: The id of the type code to be deleted. [integer]
      """
      url = "%s/services/sdm/typecodes/%s" % (self.cl.server, tcId)
      obj = self.cl.makeRequest(url, method="DELETE", objectify=True)
      return obj
    
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
   def postTypeCode(self, code, title=None, description=None, keywords=[]):
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
      for kw in keywords:
         params.append(("keyword", kw))
      url = "%s/services/sdm/typecodes" % self.cl.server
      obj = self.cl.makeRequest(url, 
                                method="post", 
                                parameters=params,
                                objectify=True).typecode
      return obj
      
   
   # --------------------------------------------------------------------------

   # .........................................
   def hint(self, query, maxReturned=None, serviceRoot=None):
      """
      @summary: Queries for occurrence sets that match the partial query string
      @param query: The partial string to match (genus species).  Must be at 
                       least 3 characters.
      @param maxReturned: (optional) The maximum number of results to return
      @param serviceRoot: (optional) The web server root for the hint service.  
                             Defaults to the instance that the object is 
                             connected to if None is provided.
      @note: This will return a list of SearchHit objects.  These are named
                tuples that have the attributes: name, id, numPoints, 
                downloadUrl and binomial.  These attributes are pulled from the 
                response from the Lucene query and may change over time.
      """
      if serviceRoot is None:
         serviceRoot = self.cl.server
         
      SearchHit = namedtuple('SearchHit', ['name', 'id', 'numPoints', 
                                           'downloadUrl', 'binomial', 
                                           'numModels'])
      if len(query) < 3:
         raise Exception, "Please provide at least 3 characters to hint service"
      
      params = [
                ("maxReturned", maxReturned),
                ("format", "json")
               ]
      url = "%s/hint/species/%s" % (serviceRoot, query)
      
      res = self.cl.makeRequest(url, method="get", parameters=params)
      
      jObj = json.loads(res)
      
      try:
         # Old json format
         jsonItems = jObj.get('columns')[0]
      except:
         # New json format
         jsonItems = jObj.get('hits')
      
      items = []
      for item in jsonItems:
         items.append(SearchHit(name=item.get('name'),
                                id=int(item.get('occurrenceSet')),
                                numPoints=int(item.get('numPoints')),
                                downloadUrl=item.get('downloadUrl'),
                                binomial=item.get('binomial'),
                                numModels=int(item.get('numModels'))))
      if maxReturned is not None and maxReturned < len(items):
         items = items[:maxReturned]
      return items
   
   # .........................................
   def searchArchive(self, query, maxReturned=None, serviceRoot=None):
      """
      @summary: Queries the Lifemapper Solr index for archive data
      @param query: The partial string to match (genus species).
      @param maxReturned: (optional) The maximum number of results to return
      @note: This will return all models and projections associated with 
                occurrence sets that match this query
      @rtype: A list of archive hits
      """
      if serviceRoot is None:
         serviceRoot = self.cl.server
      url = "%s/hint/archive/%s" % (serviceRoot, query)
      resp = self.cl.makeRequest(url, method="get", objectify=True)
      return resp.hits

   # .........................................
   def getShapefileFromOccurrencesHint(self, searchHit, filename, 
                                           instanceName=None, overwrite=False):
      """
      @summary: Downloads a shapefile from the occurrences hint service.  This
                   will start by downloading the Lifemapper shapefile but can
                   be expanded later to query the original data source.
      @param searchHit: The SearchHit named tuple returned by the hint service
      @param filename: The file location to save the shapefile
      @param instanceName: (optional) The name of the instance that the search
                              hit came from.  This can be used to determine how
                              to get the data for the resuling shapefile.
      @param overwrite: (optional) Should files be overwritten if they exist?
      @note: This code should be hardened.  It is mainly for the Spring 2015 
                iDigBio hackathon
      """
      if instanceName.lower() == Instances.IDIGBIO.lower():
         # Aimee: Edit here for iDigBio
         # The searh hit objects have documentation in the "hint" function
         # The binomial will probably be useful.  It is different than name 
         #   because name is the display name that may include author 
         #   information and binomial is just that.
         pass
      #elif instanceName.lower() == Instances.BISON.lower():
         # Add Bison processing code here
      else:
         url = searchHit.downloadUrl
         cnt = self.cl.makeRequest(url, method="GET")
         self.cl.autoUnzipShapefile(cnt, filename, overwrite=overwrite)

   # .........................................
   def getOgcEndpoint(self, obj):
      """
      @summary: Returns the OGC endpoint for a Lifemapper SDM object
      @param obj: The object to get the OGC endpoint of
      """
      endpoint = "{base}/ogc?layers={layersParam}".format(
                                                  base=obj.metadataUrl,
                                                  layersParam=obj.mapLayername)
      return endpoint
   
   # .........................................
   def validateAlgorithmParameters(self, algoParams, prjScns):
      """
      @summary: Validates algorithm parameters for posting an experiment
      @param algoParams: A list of algorithm parameter objects
      @param prjScns: A list of projection scenario ids
      @note: Throws an error if an algorithm parameter is outside of its range
      @note: Throws an error if projections are specified and parameter 
                dictates that they can't be
      """
      for param in algoParams:
         castFunc = float
         if param.type.lower() == 'integer':
            castFunc = int
         elif param.type.lower() == 'string':
            castFunc = str
            break # Can't compare easily
         
         # Look for value out of range
         if param.min is not None:
            if castFunc(param.value) < castFunc(param.min):
               raise ParameterOutOfRange(param)
         
         if param.max is not None:
            if castFunc(param.value) > castFunc(param.max):
               raise ParameterOutOfRange(param)
         
         # Look to see if there shouldn't be projections and are
         if param.allowProjectionsIfValue is not None:
            if castFunc(param.allowProjectionsIfValue) != castFunc(param.value)\
                  and len(prjScns) > 0:
               raise ProjectionsNotAllowed(param)
      
