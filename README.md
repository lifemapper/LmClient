Lifemapper Client Library
========

The Lifemapper client library provides access to Lifemapper web services

Website: http://lifemapper.org

Author: CJ Grady 

Email: cjgrady@ku.edu

Version: 3.1.0

We acknowledge the support of grant BIO/EF #0851290 from the U.S. National Science Foundation for the production of this software.

Purpose
========
   The Lifemapper client library is provided as a tool, written in Python, to
communicate with the Lifemapper web services. Additional web service
documentation can be found at: http://lifemapper.org/schemas/services.wadl

Dependencies
========
- Requires LmCommon - https://github.com/lifemapper/LmCommon
- Tested with Python 2.7
   
Configuration
========
   Once the Lifemapper client library code has been installed, it must be 
   configured.  

To configure the Lifemapper client library: 
- Copy the example-config.ini file to a location that you can edit.
- (If necessary) Edit your configuration file as needed to represent your environment.
- Set the environment variable 'LIFEMAPPER_CONFIG_FILE' to point at the location of your configuration file.
