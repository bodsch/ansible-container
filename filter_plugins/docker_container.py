# python 3 headers, required if submitting to Ansible

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.display import Display

import json
from ruamel.yaml import YAML
import itertools

display = Display()


class FilterModule(object):
    """
      ansible filter
    """

    def filters(self):
        return {
            'container_hashes': self.filter_hashes,
            'compare_dict': self.filter_compare_dict,
            'container_names': self.filter_names,
            'container_images': self.filter_images,
            'container_state': self.container_state,
            'container_volumes': self.filter_volumes,
            'container_mounts': self.filter_mounts,
            'container_ignore_state': self.container_ignore_state,
            'remove_values': self.remove_values,
            'remove_custom_fields': self.remove_custom_fields,
            'remove_source_handling': self.remove_source_handling,
            'changed': self.filter_changed,
            'properties_changed': self.filter_properties_changed,
            'update': self.filter_update,
            'files_available': self.files_available,
            'reporting': self.reporting
        }

    def filter_hashes(self, mydict):
        """
          return basic information about containers
        """
        seen = {}
        data = {}

        if (isinstance(mydict, list)):
            data = mydict['results']

        for i in data:
            if (isinstance(i, dict)):
                cont = {}
                item = {}

                if ('container' in i):
                    cont = i.get('container')
                if ('item' in i):
                    item = i.get('item')

                if (cont):
                    name = cont.get('Name').strip("/")
                    # display.vv("found: {}".format(name))
                    image         = cont.get('Config').get('Image')
                    created       = cont.get('Created')
                elif (item):
                    name = item.get('name')
                    # display.vv("found: {}".format(name))
                    image         = item.get('image')
                    created       = "None"
                else:
                    pass
            else:
                pass

            registry      = image.split('/')[0]
            container     = image.split('/')[1].split(':')[0]
            container_tag = image.split(':')[1]

            seen[name] = {
                "container": container,
                "registry": registry,
                "tag": container_tag,
                "created": created,
            }

        # display.v("return : {}".format(seen))
        return seen

    def filter_compare_dict(self, left_dict, right_dict):
        """
        """
        result = {}

        if (isinstance(left_dict, list)):
            _dict = {}

            for e in left_dict:
                name = e.get('name')
                image = e.get('image')

                registry      = image.split('/')[0]
                container     = image.split('/')[1].split(':')[0]
                container_tag = image.split(':')[1]

                _dict[name] = {
                    "container": container,
                    "registry": registry,
                    "tag": container_tag,
                    "created": "None",
                }

            left_dict = _dict

        for k in left_dict:
            l_dict = left_dict[k]
            r_dict = right_dict[k]
            _ = l_dict.pop('created')
            _ = r_dict.pop('created')

            if (k not in right_dict):
                result[k] = l_dict
            else:
                left  = json.dumps(l_dict, sort_keys=True)
                right = json.dumps(r_dict, sort_keys=True)

                if (left != right):
                    result[k] = l_dict

        # display.v("return : {}".format(result))
        return result

    def filter_names(self, data):
        """
        """
        return self._get_keys_from_dict(data, 'name')

    def filter_images(self, data):
        """
        """
        return self._get_keys_from_dict(data, 'image')

    def container_state(self, data, state, return_value):
        """
            state can be
                - absent
                - present
                - stopped
                - started ← (default)
        """
        # display.v(f"container_state(self, data, {state}, {return_value})")

        result = []
        _defaults_present = ['started', 'present']
        _defaults_absent  = ['stopped', 'absent']
        state_filter = []

        if state in _defaults_present:
            state_filter = _defaults_present
        else:
            state_filter = _defaults_absent

        for i in data:
            if isinstance(i, dict):
                _state = i.get('state', 'started')
                image  = i.get(return_value, None)

                if _state in state_filter:
                    if image:
                        result.append(image)

        display.v(f"  = result {result}")

        return result

    def remove_values(self, data, values):
        """
        """
        return self._del_keys_from_dict(data, values)

    def filter_changed(self, data):
        """
        """
        result = []
        if (isinstance(data, dict)):
            data = data['results']

        for i in data:
            if (isinstance(i, dict)):
                changed = i.get('changed', False)
                item    = i.get('item', None)

                if (changed):
                    result.append(item)

        return result

    def filter_properties_changed(self, data):
        """
        """
        result = []
        # display.v("filter_properties_changed({})".format({}))

        if (isinstance(data, dict)):
            data = data['results']

        for i in data:
            if (isinstance(i, dict)):
                changed = i.get('changed', False)
                item    = i.get('item', {}).get('name', None)

                if changed:
                    result.append(item)

        # display.v("  = result {}".format(result))

        return result

    def filter_update(self, data, update):
        """
          add recreate to changed container entry
        """
        # display.v("filter_update(data, {})".format(update))
        for change in update:
            for d in data:
                if d.get('image') == change or d.get('name') == change:
                    d['recreate'] = "true"

        return data

    def filter_volumes(self, data):
        """
          return volumes
        """
        result = []
        volumes = self._get_keys_from_dict(data, 'volumes')
        merged = list(itertools.chain(*volumes))

        #  - testing5:/var/tmp/testing5|{owner="1001",mode="0700",ignore=True}
        # local        : testing5
        # remote       : /var/tmp/testing5
        # mount        : -
        # custom_fields: {owner="1001",mode="0700",ignore=True}

        # filter volumes with this endings
        volume_block_list_ends = (
            '.pid',
            '.sock',
            '.socket',
            '.conf',
            '.config',
        )
        volume_block_list_starts = (
            '/sys',
            '/dev',
            '/run',
        )

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

            return dict(code)

        for v in merged:
            c_fields = dict()
            values = v.split('|')

            if len(values) == 2 and values[1]:
                c_fields = custom_fields(values[1])
                v = values[0]

            values = v.split(':')
            count = len(values)

            local_volume  = values[0]
            remote_volume = values[1]

            if not (
                local_volume.endswith(volume_block_list_ends) or local_volume.startswith(volume_block_list_starts)
            ):
                res = dict(
                    # docker = "{}:{}".format(values[0], values[1]) + ":{}".format(values[2]) if values[2]
                    local = local_volume,  # values[0],
                    remote = remote_volume  # values[1],
                )
                if count == 3 and values[2]:
                    res['mount'] = values[2]

                if c_fields and len(c_fields) > 0:
                    res['ansible'] = c_fields

                result.append(res)

        # display.v("return : {}".format(json.dumps(result, indent=4, sort_keys=True)))

        return result

    def filter_mounts(self, data):
        """
          return mounts
        """
        result = []
        mounts = self._get_keys_from_dict(data, 'mounts')
        merged = list(itertools.chain(*mounts))

        # remove all entries with
        # "source_handling": {
        #   "create": false
        # }
        for item in merged:
            if item.get('source_handling', {}) and item.get('source_handling', {}).get('create'):
                result.append(item)

        # display.v("return : {}".format(json.dumps(result, indent=4, sort_keys=True)))

        return result

    def container_ignore_state(self, data, ignore_states):
        """
        """
        display.v(f"container_ignore_state(self, data, {ignore_states})")

        _data = data.copy()

        result = [i for i in _data if not (i.get('state', 'started') in ignore_states)]

        return result

    def remove_custom_fields(self, data):
        """
        """
        # display.v(f"remove_custom_fields({data})")
        result = []

        if isinstance(data, list):
            for v in data:
                result.append(v.split('|')[0])
        else:
            result = data

        # display.v("return : {}".format(result))

        return result

    def remove_source_handling(self, data):
        """
        """
        # display.v(f"remove_source_handling({data})")
        if (isinstance(data, list)):
            data = self._del_keys_from_dict(data, 'source_handling')

        # display.v("return : {}".format(data))

        return data

    def files_available(self, data):
        """
        """
        result = []

        for k in data:
            if k.get('stat', {}).get('exists', False):
                result.append(k.get('item'))

        return result

    def reporting(self, data, report_for):
        """
        """
        states = []
        result = []

        if isinstance(data, dict):
            results = data.get("results", [])

            for r in results:
                failed = r.get('failed', False)
                changed = r.get('changed', False)

                if report_for == "failed" and failed:
                    states.append(r)

                if report_for == "changed" and changed:
                    states.append(r)

            # display.v(f"states: => {len(states)}")

            for item in states:
                """
                """
                data = item.get('item', {})
                name = data.get('name', None)
                hostname = data.get('hostname', None)
                image = data.get('image', None)
                msg = item.get('msg', None)

                # display.v(f" - name     {name}")
                # display.v(f" - hostname {hostname}")
                # display.v(f" - image    {image}")
                # display.v(f" - msg      {msg}")

                if report_for == "changed":
                    if hostname:
                        result.append(hostname)
                    elif name:
                        result.append(name)
                    else:
                        result.append(image)

                if report_for == "failed":
                    res = {}
                    if hostname:
                        res[hostname] = msg
                    elif name:
                        res[name] = msg
                    else:
                        res[image] = msg

                    result.append(res)

        # display.v(f"result: => {result}")

        return result

    def _get_keys_from_dict(self, dictionary, key):
        """
        """
        result = []
        for i in dictionary:
            if isinstance(i, dict):
                k = i.get(key, None)
                if k:
                    result.append(k)

        return result

    def _del_keys_from_dict(self, dictionary, key):
        """
        """
        for i in dictionary:
            if isinstance(i, dict):
                _ = i.pop(key, None)

        return dictionary
