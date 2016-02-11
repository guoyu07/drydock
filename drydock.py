#!/usr/bin/env python
import argparse
import logging
import sys

from audits.host import HostConfAudit
from audits.dock import DockerConfAudit, DockerFileAudit
from audits.containers import ContainerImgAudit, ContainerRuntimeAudit

from utils.confparse import ConfParse
from utils.output import FormattedOutput

def main():
  # Argument parsing.
  confparser = ConfParse()
  parser = argparse.ArgumentParser()

  parser.add_argument("-p", "--profile",help="Audit configuration file")
  parser.add_argument("-o", "--output",help="Output file", default="output")
  parser.add_argument("-v", "--verbosity",help="Verbosity level")
  parser.add_argument("-d", "--daemon",help="Docker daemon host <IP:port>")
  parser.add_argument("-c", "--cert",help="Client certificate")
  parser.add_argument("-k", "--key",help="Client certificate key")
  parser.add_argument("-f", "--format",help="JUnit XML or JSON", default="json")
  args = parser.parse_args()

  # Verbosity level - Default is ERROR
  if args.verbosity:
    verbosity = args.verbosity
    if verbosity == '1':
      loglevel = logging.ERROR
    elif verbosity == '2':
      loglevel = logging.WARNING
    elif verbosity == '3':
      loglevel = logging.DEBUG
  else:
    loglevel = logging.ERROR
  logging.basicConfig(level=loglevel,
                    format='%(asctime)s - %(levelname)s - %(message)s')

  # Parse format
  if args.format.lower() != 'xml' and args.format.lower() != 'json':
      logging.error("Invalid option %s - it should be either json or xml" % (args.format))
      sys.exit(1)

  # If no profile specified, switch to default
  if args.profile:
    conf = args.profile
    logging.info("Using profile %s" %(conf))
  else:
    conf = "conf/default.yml"
    logging.warning("No profile selected. Using default %s" %(conf)) 
  # If no output file is selected, switch to default
  outfile = args.output + "." + args.format
  if args.daemon:
    daemon = args.daemon
  if args.cert:
    cert = args.cert
  if args.key:
    key = args.key

  profile = confparser.load_conf(conf)
  audit_categories = {
                      'dockerconf': DockerConfAudit(),
                      'dockerfiles': DockerFileAudit(),
                      }
  if args.daemon and args.cert and args.key:
    audit_categories['host'] = HostConfAudit(url=daemon, cert=cert, key=key)
    audit_categories['container_imgs'] = ContainerImgAudit(url=daemon, cert=cert, key=key)
    audit_categories['container_runtime'] = ContainerRuntimeAudit(url=daemon, cert=cert, key=key)
  elif args.daemon:
    audit_categories['host'] = HostConfAudit(url=daemon)
    audit_categories['container_imgs'] = ContainerImgAudit(url=daemon)
    audit_categories['container_runtime'] = ContainerRuntimeAudit(url=daemon)
  else:
    audit_categories['host'] = HostConfAudit()
    audit_categories['container_imgs'] = ContainerImgAudit()
    audit_categories['container_runtime'] = ContainerRuntimeAudit()

  out = FormattedOutput(outfile, **audit_categories)
  for cat,auditclass in audit_categories.iteritems():
    if cat in profile.keys():
      try:
        auditcat = profile[cat]
        audit = auditclass
        audit.run_audits(auditcat)
        out.save_results(cat, audit.logdict)
      except KeyError:
        logging.error("No audit category '%s' defined." %cat)

  out.audit_init_info(conf)
  if args.format == 'json':
    out.write_file()
  else:
    out.write_xml_file()
  out.terminal_output()

if  __name__ =='__main__':
    main()
