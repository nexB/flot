#
# SPDX-License-Identifier: BSD-2-clause AND BSD-3-clause
# Copyright (c) 2015, Thomas Kluyver and contributors
# Copyright (c) Donald Stufft and individual contributors.
# Based on https://github.com/pypa/flit/ and heavily modified
# Regex from packaging, via PEP 440

"""Normalize version number according to PEP 440"""
import logging
import os
import re

log = logging.getLogger(__name__)

VERSION_PERMISSIVE = re.compile(
    r"""
    \s*v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
\s*$""",
    re.VERBOSE,
)

pre_spellings = {
    "a": "a",
    "alpha": "a",
    "b": "b",
    "beta": "b",
    "rc": "rc",
    "c": "rc",
    "pre": "rc",
    "preview": "rc",
}


def normalize_version(orig_version):
    """Normalise version number according to rules in PEP 440

    Raises InvalidVersion if the version does not match PEP 440. This can be
    overridden with the FLIT_ALLOW_INVALID environment variable.

    https://www.python.org/dev/peps/pep-0440/#normalization
    """
    version = orig_version.lower()
    m = VERSION_PERMISSIVE.match(version)
    if not m:
        if os.environ.get("FLIT_ALLOW_INVALID"):
            log.warning(
                "Invalid version number {!r} allowed by FLIT_ALLOW_INVALID".format(
                    orig_version
                )
            )
            return version
        else:
            from .common import InvalidVersion

            raise InvalidVersion(
                "Version number {!r} does not match PEP 440 rules".format(orig_version)
            )

    components = []
    add = components.append

    epoch, release = m.group("epoch", "release")
    if epoch is not None:
        add(str(int(epoch)) + "!")
    add(".".join(str(int(rp)) for rp in release.split(".")))

    pre_l, pre_n = m.group("pre_l", "pre_n")
    if pre_l is not None:
        pre_l = pre_spellings[pre_l]
        pre_n = "0" if pre_n is None else str(int(pre_n))
        add(pre_l + pre_n)

    post_n1, post_l, post_n2 = m.group("post_n1", "post_l", "post_n2")
    if post_n1 is not None:
        add(".post" + str(int(post_n1)))
    elif post_l is not None:
        post_n = "0" if post_n2 is None else str(int(post_n2))
        add(".post" + str(int(post_n)))

    dev_l, dev_n = m.group("dev_l", "dev_n")
    if dev_l is not None:
        dev_n = "0" if dev_n is None else str(int(dev_n))
        add(".dev" + dev_n)

    local = m.group("local")
    if local is not None:
        local = local.replace("-", ".").replace("_", ".")
        l = [str(int(c)) if c.isdigit() else c for c in local.split(".")]
        add("+" + ".".join(l))

    version = "".join(components)
    if version != orig_version:
        log.warning(
            "Version number normalised: {!r} -> {!r} (see PEP 440)".format(
                orig_version, version
            )
        )
    return version
