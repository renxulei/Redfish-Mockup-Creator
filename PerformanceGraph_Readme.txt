PerformanceGrapch generation tool based on Redfish-Mockup-Creator

Usage:

--dir		mockup payload directory, this is a common argument that is required for both local mode and co-work mode.
--expect		expect average response time, this is a common argument that is required for both local mode and co-work mode.
mockupargs	if this argument is applied, the tool will run in co-work mode.  Please put arguments that shall be passed to Redfish-Mockup-Creator after this one（except --dir）, this argument must be defined under co-work mode.

As for Redfish-Mockup-Creator usage, please refer to its README.md for details.

Usage example:

PerformanceGraph.py --dir ./Mockup/ExampleDirectory --expect 1.5 mockupargs -r 127.0.0.1 -u username -p password -M -H -A Basic
