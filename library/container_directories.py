#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function
import os
import pwd
import grp

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.lists import compare_two_lists


class ContainerDirectories(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module

        self.base_directory = module.params.get("base_directory")
        self.container = module.params.get("container")
        self.owner = module.params.get("owner")
        self.group = module.params.get("group")
        self.mode = module.params.get("mode")

    def run(self):
        """
        """
        result = dict(
            changed=False,
            failed=True,
            msg="initial"
        )

        created_directories = []

        changed = False

        if not os.path.isdir(self.base_directory):
            create_directory(directory=self.base_directory, mode="0755")

        for directory in self.container:
            d = os.path.join(self.base_directory, directory)

            if not os.path.isdir(d):
                pre = self.__analyse_directory(d)
                create_directory(
                    directory=d,
                    owner=self.owner,
                    group=self.group,
                    mode=self.mode
                )
                post = self.__analyse_directory(d)

                diff = compare_two_lists(pre, post)

                if not diff:
                    created_directories.append(d)

                if not changed and not diff:
                    changed = True

        return dict(
            changed = changed,
            failed = False,
            created_directories = created_directories
        )

        return result

    def __analyse_directory(self, directory):
        """
        """
        result = []

        res = {}

        current_owner = None
        current_group = None
        current_mode  = None

        res[directory] = {}

        if os.path.isdir(directory):
            _state = os.stat(directory)
            try:
                current_owner  = pwd.getpwuid(_state.st_uid).pw_uid
            except KeyError:
                pass
            try:
                current_group = grp.getgrgid(_state.st_gid).gr_gid
            except KeyError:
                pass
            try:
                current_mode  = oct(_state.st_mode)[-3:]
            except KeyError:
                pass

        res[directory]['owner'] = current_owner
        res[directory]['group'] = current_group
        res[directory]['mode']  = current_mode

        result.append(res)

        return result

# ===========================================
# Module execution.


def main():
    """
    """
    args = dict(
        base_directory = dict(
            required=True,
            type='str'
        ),
        container=dict(
            required=True,
            type='list'
        ),
        owner=dict(
            required=False
        ),
        group=dict(
            required=False
        ),
        mode=dict(
            required=False,
            type="str"
        ),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = ContainerDirectories(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == '__main__':
    main()
