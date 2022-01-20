#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import json
import pwd
import grp
from ruamel.yaml import YAML

from ansible.module_utils.basic import AnsibleModule

class ContainerDirectories(object):
    """
    """
    def __init__(self, module):
        """
        """
        self.module = module

        self.data = module.params.get("data")
        self.volumes = module.params.get("volumes")
        self.mounts = module.params.get("mounts")
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

        # _, _, self.uid, gid, _, _, _ = pwd.getpwnam(self.owner)
        # name, passwd, num, mem = grp.getgrnam(self.group)
        #
        # if(not num):
        #     self.gid = gid
        # else:
        #     self.gid = num

        self.uid = 1000
        self.gid = 1000

        # self.module.log(msg="------------------------------")
        # self.module.log(msg="state          {}".format(self.state))
        # self.module.log(msg="dest           {}".format(self.dest))
        # self.module.log(msg="checksum_file  {}".format(self.checksum_file))
        # self.module.log(msg="properties     {}".format(self.properties))
        # self.module.log(msg="------------------------------")

    def run(self):
        """
        """
        result = dict(
            changed=False,
            failed=True,
            msg="initial"
        )

        all_volumes = self.__volumes()
        all_mounts  = self.__mounts()

        migrated_volumes = self.__migrate_volumes(all_volumes)

        # self.module.log("mounts   : {}".format(
        #     all_mounts
        # ))
        # self.module.log("migrated : {}".format(
        #     migrated_volumes
        # ))

        full_list = migrated_volumes + all_mounts

        # self.module.log("{}".format(
        #     json.dumps(full_list, indent=4)
        # ))

        self.__create_directories(full_list)


        # # self.module.log("type: {} | {}".format(
        # #     type(self.data),
        # #     self.data
        # # ))
        #
        # for d in self.data:
        #     # self.module.log("{} | {}".format(type(d), d))
        #
        #     _n = d.get('name')
        #     _v = d.get('volumes', [])
        #     _m = d.get('mounts', [])
        #
        #     self.module.log("name: {}".format(_n))
        #     self.module.log("v   : {} | {} | {}".format(type(_v), len(_v), _v) )
        #     self.module.log("m   : {} | {} | {}".format(type(_m), len(_m), _m))
        #
        #     if len(_v.count) > 0:
        #         all_volumes.append(_v)
        #
        #     if len(_m.count) > 0:
        #         all_mounts.append(_m)
        #
        # self.module.log("volumes: {}".format(
        #     all_volumes
        # ))
        # self.module.log("mounts : {}".format(
        #     all_mounts
        # ))


        return result

    def __volumes(self):
        """
        """
        self.module.log("- __volumes()")
        all_volumes = []

        for d in self.data:
            #_n = d.get('name')
            _v = d.get('volumes', [])

            #self.module.log("name: {}".format(_n))
            #self.module.log("v   : {} | {} | {}".format(type(_v), len(_v), _v) )

            if len(_v) > 0:
                all_volumes.append(_v)

        self.module.log("volumes: {}".format(
            all_volumes
        ))

        self.module.log("return: {}".format(all_volumes))

        return all_volumes

    def __mounts(self):
        """
        """
        self.module.log("- __mounts()")
        all_mounts = []

        for d in self.data:
            #_n = d.get('name')
            _m = d.get('mounts', [])

            #self.module.log("name: {}".format(_n))
            #self.module.log("m   : {} | {} | {}".format(type(_m), len(_m), _m))

            if len(_m) > 0:
                all_mounts = _m

        self.module.log("mounts : {}".format(
            all_mounts
        ))

        self.module.log("return: {}".format(all_mounts))

        return all_mounts

    def __migrate_volumes(self, volumes):
        """
        """
        self.module.log("- __migrate_volumes(volumes)")

        result = []
        yaml = YAML()

        def custom_fields(d):
            """
              returns only custom fileds as json
            """
            #self.module.log("- custom_fields({})".format(d))

            d = d.replace('=', ': ')

            if d.startswith("[") and d.endswith("]"):
                d = d.replace("[", "")
                d = d.replace("]", "")

            if not (d.startswith("{") and d.endswith("}")):
                d = "{" + d + "}"

            code = yaml.load(d)

            for key, value in code.items():
                #self.module.log("  - {} : {}".format(key, value))
                # transform ignore=True into create=False
                if key == "ignore":
                    code.insert(0, 'create', not value)
                    del code[key]

            # self.module.log("return: {}".format(code))

            return dict(code)

        # from: /tmp/testing5:/var/tmp/testing5|{owner="1001",mode="0700",ignore=True}
        # to:
        # - source: /tmp/testing5
        #   target: /var/tmp/testing5
        #   source_handling:
        #     create: false
        #     owner: "1001"
        #     mode: "0700"
        #
        # from: /tmp/testing3:/var/tmp/testing3:rw|{owner="999",group="1000"}
        # to:
        # - source: /tmp/testing3
        #   target: /var/tmp/testing3
        #   source_handling:
        #     create: true
        #     owner: "999"
        #     group: "1000"
        #

        for d in volumes:
            # self.module.log("{} | {}".format(type(d), d))
            for entry in d:
                # self.module.log("{} | {}".format(type(entry), entry))

                read_mode = None
                c_fields = dict()
                values = entry.split('|')

                if len(values) == 2 and values[1]:
                    c_fields = custom_fields(values[1])
                    entry = values[0]

                values = entry.split(':')
                count = len(values)
                # self.module.log("{} | {}".format(count, values))

                local_volume  = values[0]
                remote_volume = values[1]

                if count == 3 and values[2]:
                    read_mode = values[2]

                if not (
                    local_volume.endswith(self.volume_block_list_ends) or
                    local_volume.startswith(self.volume_block_list_starts)
                ):
                    res = dict(
                        source = local_volume,   # values[0],
                        target = remote_volume,  # values[1],
                        type = "bind",
                        source_handling = c_fields
                    )

                    if read_mode is not None:
                        res['read_only'] = self.read_only.get(read_mode)

                    result.append(res)

            self.module.log("{} | {}".format(type(result), result))

        return result


    def __create_directories(self, directory_tree):
        """
        """
        self.module.log("  {}".format(directory_tree))

        for entry in directory_tree:
            self.module.log(" - {}".format(entry))

            source = entry.get('source')
            source_handling = entry.get('source_handling', {})
            force_create = entry.get('source_handling', {}).get('create', None)

            force_owner = entry.get('source_handling', {}).get('owner', None)
            force_group = entry.get('source_handling', {}).get('group', None)
            force_mode  = entry.get('source_handling', {}).get('mode' , None)
            # self.module.log("   - {}".format(force_create))

            self.module.log(" -> {}".format(source))
            if force_create is not None and not force_create:
                self.module.log("   ignore")
                # continue
                pass
            else:
                self.module.log("   create")
                try:
                    os.makedirs(source, exist_ok=True)
                except FileExistsError:
                    pass

            if force_owner is not None or force_group is not None:
                self.module.log("   - {} : {}".format(force_owner, force_group))

                if force_owner is not None:
                    try:
                        u = pwd.getpwnam(force_owner).pw_uid
                    except KeyError:
                        u = int(force_owner)

                    self.module.log("   uid: {}".format(u))

                if force_group is not None:
                    try:
                        g = grp.getgrnam(force_group).gr_gid
                    except KeyError:
                        g = int(force_group)

                    self.module.log("   gid: {}".format(g))

                # os.chown(source, int(force_owner), int(force_group))

                if(force_mode is not None):
                    os.chmod(
                        source, int(force_mode, base=8)
                    )

        # for path in directory_tree:
        #     try:
        #         os.makedirs(path, exist_ok=True)
        #     except FileExistsError:
        #         pass
        #
        # if(self.uid and self.gid):
        #     for root, dirs, files in os.walk("/{}".format(self.base_directory.split('/')[1])):
        #         for d in dirs:
        #             os.chown(os.path.join(root, d), self.uid, self.gid)
        #             if(self.mode):
        #                 os.chmod(
        #                     os.path.join(root, d),
        #                     int(self.mode, base=8))


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
