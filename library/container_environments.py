#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import hashlib
import json

from ansible.module_utils.basic import AnsibleModule


class ContainerEnvironments(object):
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

        result_state = []

        for c in self.container:
            """
            """
            name = c.get("name")
            environments  = c.get("environments", {})
            properties = c.get("properties", {})
            changed = False
            e_changed = False
            p_changed = False

            state = []

            # e_changed = self._write_environments(name, environments)

            # self.module.log("name: {0}".format(name))
            # if len(environments) > 0:
            """
              write environments
            """
            e_changed = self._write_environments(name, environments)

            if len(environments) > 0:
                _ = c.pop("environments")

            state.append("environment")

            if len(properties) > 0:
                """
                  write properties
                """
                p_changed = self._write_properties(name, properties)
                _ = c.pop("properties")

                state.append("properties")

            if e_changed or p_changed:
                changed = True

            if changed:
                # add recreate to dictionary
                c['recreate'] = True

                res = {}
                state = " and ".join(state)
                state += " successful written"

                res[name] = dict(
                    # changed=True,
                    state=state
                )

                result_state.append(res)

        # define changed for the running tasks
        # migrate a list of dict into dict
        combined_d = {key: value for d in result_state for key, value in d.items()}
        # find all changed and define our variable
        # changed = (len({k: v for k, v in combined_d.items() if v.get('changed') and v.get('changed') == True}) > 0) == True
        changed = (len({k: v for k, v in combined_d.items() if v.get('state')}) > 0)

        result = dict(
            changed = changed,
            failed = False,
            container_data = self.container,
            state = result_state
        )

        return result

    def _write_environments(self, name, environments = {}):
        """
        """
        checksum_file = os.path.join(self.base_directory, name, ".container.env.checksum")
        data_file     = os.path.join(self.base_directory, name, "container.env")

        return self.__write_file(environments, "environments", data_file, checksum_file)

    def _write_properties(self, name, properties = {}):
        """
        """
        if len(properties) == 0:
            return False

        checksum_file = os.path.join(self.base_directory, name, ".{}.properties.checksum".format(name))
        data_file     = os.path.join(self.base_directory, name, "{}.properties".format(name))

        return self.__write_file(properties, "properties", data_file, checksum_file)

    def __write_file(self, data, env, data_file, checksum_file):
        """
        """
        _old_checksum = ""

        if os.path.exists(checksum_file):
            with open(checksum_file, "r") as f:
                _old_checksum = f.readlines()[0]

        data = self.__template(data, env)
        checksum = self.__checksum(data)

        data_up2date = (_old_checksum == checksum)

        # self.module.log(msg=" - new  checksum '{}'".format(checksum))
        # self.module.log(msg=" - curr checksum '{}'".format(_old_checksum))
        # self.module.log(msg=" - up2date       '{}'".format(data_up2date))

        if data_up2date:
            return False

        with open(data_file, "w") as f:
            f.write(data)

            with open(checksum_file, "w") as f:
                f.write(checksum)

        return True

    def __checksum(self, plaintext):
        """
        """
        if isinstance(plaintext, dict):
            password_bytes = json.dumps(plaintext, sort_keys=True).encode('utf-8')
        else:
            password_bytes = plaintext.encode('utf-8')

        password_hash = hashlib.sha256(password_bytes)
        return password_hash.hexdigest()

    def __template(self, data, env):
        """
          generate data from dictionary
        """
        if env == "environments":
            tpl = """
#jinja2: trim_blocks: True, lstrip_blocks: True
# generated by ansible
# {{ item }}
{%- for key, value in item.items() %}
{{ key }}={{ value }}
{%- endfor %}
# ---
# EOF

"""
        if env == "properties":
            tpl = """
#jinja2: trim_blocks: True, lstrip_blocks: True
# generated by ansible
{%- for key, value in item.items() %}
{{ key.ljust(30) }} = {{ value }}
{%- endfor %}

"""

        from jinja2 import Template

        tm = Template(tpl)
        d = tm.render(item=data)

        return d

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
            container = dict(
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

    p = ContainerEnvironments(module)
    result = p.run()

    # module.log(msg="= result: {}".format(result))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
