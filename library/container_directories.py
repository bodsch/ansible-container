#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import pwd
import grp

from ansible.module_utils.basic import AnsibleModule


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
            self.__create_directory(directory=self.base_directory, mode="0755")

        for directory in self.container:
            d = os.path.join(self.base_directory, directory)

            self.module.log("  - {}".format(d))

            if not os.path.isdir(d):
                pre = self.__analyse_directory(d)
                self.__create_directory(
                    directory=d,
                    owner=self.owner,
                    group=self.group,
                    mode=self.mode
                )
                post = self.__analyse_directory(d)

                # self.module.log(" - {}".format(pre))
                # self.module.log(" - {}".format(post))

                diff = self.__compare_two_lists(pre, post)

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
        # self.module.log("- __analyse_directories(directory_tree)")
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

    def __create_directory(self, directory, owner = None, group = None, mode = None):
        """
        """
        self.module.log("- __create_directory({},{},{},{})".format(directory, owner, group, mode))

        try:
            os.makedirs(directory, exist_ok=True)
        except FileExistsError:
            pass

        if mode is not None:
            os.chmod(directory, int(mode, base=8))

        if owner is not None:
            try:
                owner = pwd.getpwnam(owner).pw_uid
            except KeyError:
                owner = int(owner)
                pass
        else:
            owner = 0

        if group is not None:
            try:
                group = grp.getgrnam(group).gr_gid
            except KeyError:
                group = int(group)
                pass
        else:
            group = 0

        os.chown(directory, int(owner), int(group))

        return

    def __compare_two_lists(self, list1: list, list2: list):
        """
        Compare two lists and logs the difference.
        :param list1: first list.
        :param list2: second list.
        :return:      if there is difference between both lists.
        """
        # [i for i in list1 + list2 if i not in list1 or i not in list2]
        diff = [x for x in list2 if x not in list1]

        # self.module.log("  {0}".format(diff))
        # self.module.log("  {0}".format(diff[:5]))

        result = len(diff) == 0
        if not result:
            self.module.log("There are {0} differences:".format(len(diff)))
            self.module.log("  {0}".format(diff[:5]))
        return result

# ===========================================
# Module execution.


def main():
    """
    """
    module = AnsibleModule(
        argument_spec=dict(
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
        ),
        supports_check_mode=True,
    )

    p = ContainerDirectories(module)
    result = p.run()

    module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
