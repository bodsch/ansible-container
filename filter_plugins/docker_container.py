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
            'container_volumes': self.filter_volumes,
            'remove_values': self.remove_values,
            'remove_custom_fields': self.remove_custom_fields,
            'changed': self.filter_changed,
            'update': self.filter_update,
        }

    def filter_hashes(self, mydict):
        """
          return basic information about containers
        """
        seen = {}
        data = {}

        if(isinstance(mydict, list)):
            data = mydict['results']

        for i in data:
            if(isinstance(i, dict)):
                cont = {}
                item = {}

                if('container' in i):
                    cont = i.get('container')
                if('item' in i):
                    item = i.get('item')

                if(cont):
                    name = cont.get('Name').strip("/")
                    display.vv("found: {}".format(name))

                    image         = cont.get('Config').get('Image')
                    created       = cont.get('Created')
                elif(item):
                    name = item.get('name')
                    display.vv("found: {}".format(name))

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

        display.v("return : {}".format(seen))

        return seen

    def filter_compare_dict(self, left_dict, right_dict):
        result = {}

        if(isinstance(left_dict, list)):
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

                if(left != right):
                    result[k] = l_dict

        display.v("return : {}".format(result))

        return result

    def filter_names(self, data):
        """
        """
        return self._get_keys_from_dict(data, 'name')

    def filter_images(self, data):
        """
        """
        return self._get_keys_from_dict(data, 'image')

    def remove_values(self, data, values):
        """
        """
        return self._del_keys_from_dict(data, values)

    def filter_changed(self, data):
        """
        """
        result = []
        if(isinstance(data, dict)):
            data = data['results']

        for i in data:
            if(isinstance(i, dict)):
                changed = i.get('changed', False)
                item    = i.get('item', None)

                if(changed):
                    result.append(item)

        return result

    def filter_update(self, data, update):
        """
          add recreate to changed container entry
        """
        for change in update:
            for d in data:
                if(d.get('image') == change):
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

        display.v("return : {}".format(json.dumps(result, indent=4, sort_keys=True)))

        return result

    def remove_custom_fields(self, data):
        """

        """
        result = []

        if isinstance(data, list):
            for v in data:
                result.append(v.split('|')[0])
        else:
            result = data

        return result

    def _get_keys_from_dict(self, dictionary, key):
        """
        """
        result = []
        for i in dictionary:
            if(isinstance(i, dict)):
                k = i.get(key, None)
                if(k):
                    result.append(k)

        return result

    def _del_keys_from_dict(self, dictionary, key):
        """
        """
        for i in dictionary:
            if(isinstance(i, dict)):
                _ = i.pop(key, None)

        return dictionary
