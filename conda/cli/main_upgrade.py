# (c) 2012 Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
#
# conda is distributed under the terms of the BSD 3-clause license.
# Consult LICENSE.txt or http://opensource.org/licenses/BSD-3-Clause.

import logging

from anaconda import anaconda
from package_plan import package_plan


log = logging.getLogger(__name__)


def configure_parser(sub_parsers):
    p = sub_parsers.add_parser(
        'upgrade',
        description     = "Upgrade Anaconda CE install to full Anaconda trial.",
        help            = "Upgrade Anaconda CE install to full Anaconda trial.",
    )
    p.add_argument(
        "--confirm",
        action  = "store",
        default = "yes",
        choices = ["yes", "no"],
        help    = "ask for confirmation before upgrading packages (default: yes)",
    )
    p.add_argument(
        "--dry-run",
        action  = "store_true",
        default = False,
        help    = "display packages to be modified, without actually executing",
    )
    p.set_defaults(func=execute)


def execute(args):
    conda = anaconda()

    if conda.target == 'pro':
        print "Full Anaconda already activated!"
        return

    idx = conda.index

    env = conda.default_environment
    env_reqs = env.get_requirements('pro')

    candidates = idx.lookup_from_name('anaconda')
    candidates = idx.find_matches(env_reqs, candidates)
    pkg = max(candidates)

    log.debug('anaconda version to upgrade to: %s' % pkg.canonical_name)

    plan = package_plan()

    all_pkgs = set([pkg])
    for spec in pkg.requires:
        canonical_name = "%s-%s-%s" % (spec.name, spec.version.vstring, spec.build)
        all_pkgs.add(conda.index.lookup_from_canonical_name(canonical_name))

    # download any packages that are not available
    for pkg in all_pkgs:

        # download any currently unavailable packages
        if pkg not in env.conda.available_packages:
            plan.downloads.add(pkg)

        # see if the package is already active
        active = env.find_activated_package(pkg.name)
        # need to compare canonical names since ce/pro packages might compare equal
        if active and pkg.canonical_name != active.canonical_name:
            plan.deactivations.add(active)

        if pkg not in env.activated:
            plan.activations.add(pkg)

    print "Upgrading Anaconda CE installation to full Anaconda"

    print plan

    if args.dry_run: return

    if args.confirm == "yes":
        proceed = raw_input("Proceed (y/n)? ")
        if proceed.lower() not in ['y', 'yes']: return

    plan.execute(env)
