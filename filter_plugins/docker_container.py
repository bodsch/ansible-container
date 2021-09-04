# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.display import Display

import json
from ruamel.yaml import YAML
import itertools

# https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html
# https://blog.oddbit.com/post/2019-04-25-writing-ansible-filter-plugins/

display = Display()


class FilterModule(object):
    ''' Ansible file jinja2 tests '''

    def filters(self):
        return {
            'container_hashes': self.filter_hashes,
            'compare_dict': self.filter_compare_dict,
            'container_names': self.filter_names,
            'container_images': self.filter_images,
            'container_volumes': self.filter_volumes,
            'remove_custom_fields': self.remove_custom_fields,
            'remove_environments': self.filter_remove_env,
            'changed': self.filter_changed,
            'update': self.filter_update,
        }

    """
      return basic information about containers
    """

    def filter_hashes(self, mydict):
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

                # display.vv("cont: {}".format(cont))
                # display.vv("item: {}".format(item))
                # display.vv("images: {}".format(images))

                if(cont):
                    # for x in ['HostConfig', 'State', 'GraphDriver', 'NetworkSettings']:
                    #    _ = container.pop(x)
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

            display.v("rebuild left")
            _dict = {}

            # display.vv(json.dumps(left_dict, indent = 2))

            for e in left_dict:
                display.v("  {}".format(e))
                display.v("  {}".format(e.get('name')))
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

        display.vv("left")
        display.vv(json.dumps(left_dict, indent = 2))
        display.vv("right")
        display.vv(json.dumps(right_dict, indent = 2))

        for k in left_dict:
            display.v("  {}".format(k))

            l_dict = left_dict[k]
            r_dict = right_dict[k]
            _ = l_dict.pop('created')
            _ = r_dict.pop('created')

            if (k not in right_dict):
                result[k] = l_dict
            else:
                left  = json.dumps(l_dict, sort_keys=True)
                right = json.dumps(r_dict, sort_keys=True)

                display.v(json.dumps(left, indent = 2))
                display.v(json.dumps(right, indent = 2))

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

    def filter_remove_env(self, data):
        """

        """
        return self._del_keys_from_dict(data, 'environments')

    def filter_changed(self, data):
        """

        """
        result = []

        # display.v( "{}".format(type(data)))

        if(isinstance(data, dict)):
            data = data['results']

        for i in data:
            # display.v( json.dumps( i, indent = 2 ) )

            # display.v("name   : {}".format(i.get('item')))
            # display.v("  -    : {}".format(i.get('image',{}).get('ContainerConfig',{}).get('Image',None) ))
            # display.v("  -    : {}".format(i.get('image',{}).get('Config',{}).get('Image',None) ))

            if(isinstance(i, dict)):
                changed = i.get('changed', False)
                item    = i.get('item', None)
                display.vv("item   : {}".format(item))
                display.vv("changed: {}".format(changed))
                display.vv("actions: {}".format(i.get('actions', None)))

                if(changed):
                    result.append(item)

        # display.v("return : {}".format(result))

        return result

    def filter_update(self, data, update):
        """
          add recreate to changed container entry
        """
        # display.v("filter_update()")
        # display.v( json.dumps( data, indent = 2 ) )
        # display.v( json.dumps( update, indent = 2 ) )
        for change in update:
            for d in data:
                if(d.get('image') == change):
                    # display.v( json.dumps( d, indent = 2 ) )
                    d['recreate'] = "true"

        return data

    def filter_volumes(self, data):
        """
          return volumes
        """
        result = []
        volumes = self._get_keys_from_dict(data, 'volumes')
        merged = list(itertools.chain(*volumes))

        # filter volumes with this endings
        volume_block_list_ends = (
            '.pid',
            '.sock',
            '.socket',
        )
        volume_block_list_starts = (
            '/sys',
            '/dev',
        )

        yaml = YAML()

        def custom_fields(d):
            d = d.replace('=', ': ')

            if d.startswith("[") and d.endswith("]"):
                d = d.replace("[", "")
                d = d.replace("]", "")

            if not (d.startswith("{") and d.endswith("}")):
                d = "{" + d + "}"

            code = yaml.load(d)

            return dict(code)

        for v in merged:
            values = v.split('|')

            c_fields = dict()

            if len(values) == 2 and values[1]:
                c_fields = custom_fields(values[1])

            values = v.split(':')
            count = len(values)

            display.v("count : {}".format(count))

            local_volume = values[0]
            if not (
                local_volume.endswith(volume_block_list_ends) or local_volume.startswith(volume_block_list_starts)
            ):
                res = dict(
                    # docker = "{}:{}".format(values[0], values[1]) + ":{}".format(values[2]) if values[2]
                    local = values[0],
                    remote = values[1],
                )
                if count == 3 and values[2]:
                    res['mount'] = values[2]

                if c_fields and len(c_fields) > 0:
                    res['ansible'] = c_fields

                result.append(res)

        display.v("return : {}".format(result))

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

    def _flatten(t):
        return [item for sublist in t for item in sublist]

    def diff_dicts(self, a, b, missing=KeyError):
        """
        Find keys and values which differ from `a` to `b` as a dict.

        If a value differs from `a` to `b` then the value in the returned dict will
        be: `(a_value, b_value)`. If either is missing then the token from
        `missing` will be used instead.

        :param a: The from dict
        :param b: The to dict
        :param missing: A token used to indicate the dict did not include this key
        :return: A dict of keys to tuples with the matching value from a and b
        """
        return {
            key: (a.get(key, missing), b.get(key, missing))
            for key in dict(
                set(a.items()) ^ set(b.items())
            ).keys()
        }

    def recursive_compare(self, d1, d2, level='root'):
        if isinstance(d1, dict) and isinstance(d2, dict):
            if d1.keys() != d2.keys():
                s1 = set(d1.keys())
                s2 = set(d2.keys())
                print('{:<20} + {} - {}'.format(level, s1 - s2, s2 - s1))
                common_keys = s1 & s2
            else:
                common_keys = set(d1.keys())

            for k in common_keys:
                self.recursive_compare(d1[k], d2[k], level='{}.{}'.format(level, k))

        elif isinstance(d1, list) and isinstance(d2, list):
            if len(d1) != len(d2):
                print('{:<20} len1={}; len2={}'.format(level, len(d1), len(d2)))
            common_len = min(len(d1), len(d2))

            for i in range(common_len):
                self.recursive_compare(d1[i], d2[i], level='{}[{}]'.format(level, i))

        else:
            if d1 != d2:
                print('{:<20} {} != {}'.format(level, d1, d2))

    def _get_keys_from_dict(self, dictionary, key):
        result = []
        for i in dictionary:
            if(isinstance(i, dict)):
                k = i.get(key, None)
                if(k):
                    display.v("=> {}".format(k))
                    result.append(k)

        return result

    def _del_keys_from_dict(self, dictionary, key):
        """

        """
        for i in dictionary:
            if(isinstance(i, dict)):
                _ = i.pop(key, None)

        return dictionary
