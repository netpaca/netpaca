# Network Automation Toolkit for Monitoring Applications

**UNDER DEVELOPMENT**

As a Developer of network automation systems, I want to be able to collect any
metric type information from my network devices and export them into a
time-series database so that I can then use this data in monitoring and
reporting applications such as Grafana.

A _*metric*_ is any data item that can be represented as a number or string
value.  A common example of a metric is a interface transmit-byte counter.
Another example is the status of a BGP neighbor interface, a value that could be
stored as a string such as "established", or stored as a number to represent
that state.  As the Developer of the monitoring application, you have the choice
and control of what you want to collect and how you want to represent that
metric to be used by your monitoring application.

A metric **is not** used to store tabular information, such a list of MAC-addresses or
routing entries.  The `nwkatk-netmon` framework was not specifically designed to support
these types of collections.  That said, it may be possible to use this framework for that
purpose; but it is not tested for such use.

# General Architecture

The design goals of this framework is to allow the Developer complete choice and
control on every aspect, including how to package and distribute Collectors,
Device-Drivers, and Exporters.  While the `nwkatk-netmon` package does include a
collector for Interface DOM metrics, the actual code could have been packaged
separately. Further, the specific support for Cisco NXAPI and Arista EOS EAPI
device-drivers could have been packaged separately.  The `nwkatk-netmon`
framework uses a dynmaic importing mechanism that is based on the standard
Python [setuptools](https://setuptools.readthedocs.io) package.  More
information about the approach and usages of `nwkatk-netmon` will be documented
shortly.  Stay tuned!
