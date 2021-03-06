#!/usr/bin/env python
# ===========
# pysap - Python library for crafting SAP's network protocols packets
#
# SECUREAUTH LABS. Copyright (C) 2019 SecureAuth Corporation. All rights reserved.
#
# The library was designed and developed by Martin Gallo from
# the SecureAuth Labs team.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# ==============

# Standard imports
import logging
from optparse import OptionParser, OptionGroup
# External imports
from scapy.config import conf
# Custom imports
import pysap
from pysap.SAPRouter import SAPRoutedStreamSocket
from pysap.SAPMS import SAPMS, ms_dump_command_values, ms_opcode_error_values, ms_domain_values_inv


# Set the verbosity to 0
conf.verb = 0


# Command line options parser
def parse_options():

    description = "This example script gather information provided by a SAP Netweaver Application Server with the " \
                  "Message Server protocol using the Dump command. Execution of the dump commands require accessing " \
                  "the internal Message Server port."

    epilog = "pysap %(version)s - %(url)s - %(repo)s" % {"version": pysap.__version__,
                                                         "url": pysap.__url__,
                                                         "repo": pysap.__repo__}

    usage = "Usage: %prog [options] -d <remote host>"

    parser = OptionParser(usage=usage, description=description, epilog=epilog)

    target = OptionGroup(parser, "Target")
    target.add_option("-d", "--remote-host", dest="remote_host",
                      help="Remote host")
    target.add_option("-p", "--remote-port", dest="remote_port", type="int", default=3900,
                      help="Remote port [%default]")
    target.add_option("--route-string", dest="route_string",
                      help="Route string for connecting through a SAP Router")
    target.add_option("--domain", dest="domain", default="ABAP",
                      help="Domain to connect to (ABAP, J2EE or JSTARTUP) [%default]")
    parser.add_option_group(target)

    misc = OptionGroup(parser, "Misc options")
    misc.add_option("-c", "--client", dest="client", default="pysap's-dumper",
                    help="Client name [%default]")
    misc.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                    help="Verbose output [%default]")
    parser.add_option_group(misc)

    (options, _) = parser.parse_args()

    if not (options.remote_host or options.route_string):
        parser.error("Remote host or route string is required")
    if options.domain not in ms_domain_values_inv.keys():
        parser.error("Invalid domain specified")

    return options


# Main function
def main():
    options = parse_options()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    domain = ms_domain_values_inv[options.domain]

    # Initiate the connection
    conn = SAPRoutedStreamSocket.get_nisocket(options.remote_host,
                                              options.remote_port,
                                              options.route_string,
                                              base_cls=SAPMS)
    print("[*] Connected to the message server %s:%d" % (options.remote_host, options.remote_port))

    client_string = options.client

    # Send MS_LOGIN_2 packet
    p = SAPMS(flag=0x00, iflag=0x08, domain=domain, toname=client_string, fromname=client_string)

    print("[*] Sending login packet:")
    response = conn.sr(p)[SAPMS]

    print("[*] Login OK, Server string: %s" % response.fromname)
    server_string = response.fromname

    # Send a Dump Info packet for each possible Dump
    for i in ms_dump_command_values.keys():

        # Skip MS_DUMP_MSADM and MS_DUMP_COUNTER commands as the info
        # is included in other dump commands
        if i in [1, 12]:
            continue

        p = SAPMS(flag=0x02, iflag=0x01, domain=domain, toname=server_string,
                  fromname=client_string, opcode=0x1e, dump_dest=0x02,
                  dump_command=i)

        print("[*] Sending dump info", ms_dump_command_values[i])
        response = conn.sr(p)[SAPMS]

        if response.opcode_error != 0:
            print("Error:", ms_opcode_error_values[response.opcode_error])
        print(response.opcode_value)


if __name__ == "__main__":
    main()
