#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

import grp
# import json
import os
import pwd
from ansible.module_utils.basic import AnsibleModule
from ruamel.yaml import YAML


class ContainerMounts(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module

        self.data = module.params.get("data")
        self.volumes = module.params.get("volumes")
        self.mounts = module.params.get("mounts")
        self.debug = module.params.get("debug")
        self.owner = module.params.get("owner")
        self.group = module.params.get("group")
        self.mode = module.params.get("mode")

        self.volume_block_list_ends = (
            '.pid',
            '.sock',
            '.socket',
            '.conf',
            '.config',
        )
        self.volume_block_list_starts = (
            '/sys',
            '/dev',
            '/run',
        )

        self.read_only = {
            'rw': False,
            'ro': True
        }

    def run(self):
        """
        """
        result = dict(
            changed=False,
            failed=True,
            msg="initial"
        )

        all_mounts = []
        all_volumes = []
        migrated_volumes = []

        if self.volumes:
            all_volumes = self.__volumes()
            migrated_volumes = self.__migrate_volumes_to_mounts(all_volumes)

        if self.mounts:
            all_mounts = self.__mounts()

        full_list = migrated_volumes + all_mounts

        if len(full_list) == 0:
            return dict(
                changed=False,
                failed=False,
                msg="nothing to do"
            )

        current_state = self.__analyse_directories(full_list)
        self.__create_directories(full_list, current_state)
        final_state = self.__analyse_directories(full_list)

        equal_lists, diff = self.__compare_two_lists(list1=current_state, list2=final_state)

        # TODO
        # remove custom fields from 'volumes'
        if not equal_lists:
            result['msg'] = "changed or created directories"
            msg = ""
            for i in diff:
                msg += "- {0}\n".format(i)
            result['created_directories'] = msg

        if len(diff) == 0:
            result['msg'] = "nothing to do"

        result['changed'] = not equal_lists
        result['failed'] = False

        return result

    def __volumes(self):
        """
          return all volume definitions
        """
        all_volumes = []

        for d in self.data:
            _v = d.get('volumes', [])
            if len(_v) > 0:
                all_volumes.append(_v)

        return all_volumes

    def __mounts(self):
        """
          get only mountspoint when we add source_handling and set create to True
        """
        all_mounts = []

        for d in self.data:
            """
            """
            if self.debug:
                self.module.log(f"- {d.get('name')}")

            mount_defintions = d.get('mounts', [])

            for mount in mount_defintions:
                if self.debug:
                    self.module.log(f"  mount: {mount}")

                source_handling = mount.get('source_handling', {}).get("create", False)

                if len(mount_defintions) > 0 and source_handling:
                    all_mounts.append(mount)

        return all_mounts

    def __migrate_volumes_to_mounts(self, volumes):
        """
            migrate old volume definition into mount
            ignore some definitions like:
              - *.sock
              - *.conf
            etc. see self.volume_block_list_ends and self.volume_block_list_starts!

            for example:
              from: /tmp/testing5:/var/tmp/testing5|{owner="1001",mode="0700",ignore=True}
              to:
              - source: /tmp/testing5
                target: /var/tmp/testing5
                source_handling:
                  create: false
                  owner: "1001"
                  mode: "0700"

              from: /tmp/testing3:/var/tmp/testing3:rw|{owner="999",group="1000"}
              to:
              - source: /tmp/testing3
                target: /var/tmp/testing3
                source_handling:
                  create: true
                  owner: "999"
                  group: "1000"
        """
        if self.debug:
            self.module.log("__migrate_volumes_to_mounts(volumes)")

        result = []
        yaml = YAML()

        def custom_fields(d):
            """
              returns only custom fileds as json
            """
            d = d.replace('=', ': ')

            if d.startswith("[") and d.endswith("]"):
                d = d.replace("[", "")
                d = d.replace("]", "")

            if not (d.startswith("{") and d.endswith("}")):
                d = "{" + d + "}"

            code = yaml.load(d)

            for key, value in code.items():
                # transform ignore=True into create=False
                if key == "ignore":
                    code.insert(0, 'create', not value)
                    del code[key]

            if self.debug:
                self.module.log(f"    custom_fields: {dict(code)}")

            return dict(code)

        for d in volumes:
            for entry in d:
                """
                """
                if self.debug:
                    self.module.log(f"  - {entry}")

                read_mode = None
                c_fields = dict()
                values = entry.split('|')

                if len(values) == 2 and values[1]:
                    c_fields = custom_fields(values[1])
                    entry = values[0]

                values = entry.split(':')
                count = len(values)

                local_volume = values[0]
                remote_volume = values[1]

                if count == 3 and values[2]:
                    read_mode = values[2]

                valid = (local_volume.endswith(self.volume_block_list_ends) or local_volume.startswith(
                    self.volume_block_list_starts))

                if not valid:
                    """
                    """
                    res = dict(
                        source=local_volume,   # values[0],
                        target=remote_volume,  # values[1],
                        type="bind",
                        source_handling=c_fields
                    )

                    if read_mode is not None:
                        res['read_only'] = self.read_only.get(read_mode)

                    result.append(res)

        return result

    def __analyse_directories(self, directory_tree):
        """
          set current owner, group and mode to source entry
        """
        result = []
        for entry in directory_tree:
            """
            """
            res = {}

            source = entry.get('source')
            current_owner = None
            current_group = None
            current_mode = None

            res[source] = {}

            if os.path.isdir(source):
                if self.debug:
                    self.module.log(f"- {source}")
                _state = os.stat(source)
                try:
                    current_owner = pwd.getpwuid(_state.st_uid).pw_uid
                except KeyError as e:
                    if self.debug:
                        self.module.log(f"  {e}")
                    pass

                try:
                    current_group = grp.getgrgid(_state.st_gid).gr_gid
                except KeyError as e:
                    if self.debug:
                        self.module.log(f"  {e}")
                    pass

                try:
                    current_mode = oct(_state.st_mode)[-3:]
                except KeyError as e:
                    if self.debug:
                        self.module.log(f"  {e}")
                    pass

            res[source]['owner'] = current_owner
            res[source]['group'] = current_group
            res[source]['mode'] = current_mode

            result.append(res)

        return result

    def __create_directories(self, directory_tree, current_state):
        """
        """
        for entry in directory_tree:
            """
            """
            source = entry.get('source')
            source_handling = entry.get('source_handling', {})
            force_create = source_handling.get('create', None)
            force_owner = source_handling.get('owner', None)
            force_group = source_handling.get('group', None)
            force_mode = source_handling.get('mode', None)

            curr = self.__find_in_list(current_state, source)

            current_owner = curr[source].get('owner')
            current_group = curr[source].get('group')

            # create directory
            if force_create is not None and not force_create:
                pass
            else:
                try:
                    os.makedirs(source, exist_ok=True)
                except FileExistsError:
                    pass

            # change mode
            if os.path.isdir(source) and force_mode is not None:
                if isinstance(force_mode, int):
                    mode = int(str(force_mode), base=8)
                if isinstance(force_mode, str):
                    mode = int(force_mode, base=8)

                os.chmod(source, mode)

            # change ownership
            if force_owner is not None or force_group is not None:
                """
                """
                if os.path.isdir(source):
                    """
                    """
                    if force_owner is not None:
                        try:
                            force_owner = pwd.getpwnam(str(force_owner)).pw_uid
                        except KeyError:
                            force_owner = int(force_owner)
                            pass
                    elif current_owner is not None:
                        force_owner = current_owner
                    else:
                        force_owner = 0

                    if force_group is not None:
                        try:
                            force_group = grp.getgrnam(str(force_group)).gr_gid
                        except KeyError:
                            force_group = int(force_group)
                            pass
                    elif current_group is not None:
                        force_group = current_group
                    else:
                        force_group = 0

                    os.chown(source, int(force_owner), int(force_group))

    def __find_in_list(self, list, value):
        """
        """
        for entry in list:
            for k, v in entry.items():
                if k == value:
                    return entry

        return None

    def __compare_two_lists(self, list1: list, list2: list):
        """
        Compare two lists and logs the difference.
        :param list1: first list.
        :param list2: second list.
        :return:      if there is difference between both lists.
        """
        # [i for i in list1 + list2 if i not in list1 or i not in list2]
        diff = [x for x in list2 if x not in list1]

        result = len(diff) == 0
        if self.debug:
            if not result:
                self.module.log(f"There are {len(diff)} differences:")
                self.module.log(f"  {diff[:5]}")

        return result, diff


# ===========================================
# Module execution.

def main():
    module = AnsibleModule(
        argument_spec=dict(
            data=dict(
                required=True,
                type='list'
            ),
            volumes=dict(
                required=True,
                type='bool'
            ),
            mounts=dict(
                required=True,
                type='bool'
            ),
            debug=dict(
                required=False,
                default=False,
                type='bool'
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

    p = ContainerMounts(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
