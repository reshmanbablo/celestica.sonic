#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# facts_utils
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    remove_empties,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    run_commands,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.conv_utils import (
    translate,
)
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn

from ansible.utils.display import Display
display = Display()

class SonicFactsClickCli(object):

    # Constructor
    def __init__(self, facts_inst, meta_ref):
        self.facts_inst = facts_inst
        self.meta_ref = meta_ref

    # Process db_translate_method
    def process_db_translate_method(self, val, method):
        result = None
        db_method = None
        db_val = val.get(cmn.DB_VAL_NAME)

        # Invoke translate
        translated_val = translate(method, db_val)
        if translated_val:
            result = {cmn.DB_VAL_TRANSLATED_NAME: translated_val}

        return result

    # Populate meta_data values from db entries of list
    def process_db_list(self, node, entries):
        result = dict()
        facts = list()
        #display.vvv("process_db_list(), node: %s, entries: %s" % (node, entries))
        for k, v in entries.items():
            key_parts = k.split('|')
            if not key_parts:
                continue
            count = 0
            #display.vvv("process_db_list(), k: %s, v: %s, key_parts: %s" % (k, v, key_parts))
            tmp_entry = dict()
            tmp_facts = dict()
            for node_key, node_val in node.items():
                #display.vvv("process_db_list(), node_key: %s, node_val: %s" % (node_key, node_val))
                if cmn.is_meta_attr(node_key):
                    tmp_entry[node_key] = node_val
                    continue
                if count < len(key_parts):
                    db_val = {cmn.DB_VAL_NAME: key_parts[count]}
                    tmp_entry[node_key] = db_val
                    cmn.copy_meta_attrs(node_val, tmp_entry[node_key])
                    tmp_facts[node_key] = key_parts[count]
                    count += 1
                    continue
                if cmn.DB_FIELD_NAME in node_val and node_val[cmn.DB_FIELD_NAME] in v:
                    db_val = {cmn.DB_VAL_NAME: v[node_val[cmn.DB_FIELD_NAME]]}
                    tmp_entry[node_key] = db_val
                    cmn.copy_meta_attrs(node_val, tmp_entry[node_key])
                    tmp_facts[node_key] = v[node_val[cmn.DB_FIELD_NAME]]
                    #display.vvv("process_db_list(), Adding node_key: %s, db_val: %s" % (node_key, db_val))
                else: pass
            if tmp_entry:
                #display.vvv("process_db_list(), tmp_entry: %s" % (tmp_entry))
                result.update({k: tmp_entry})
            if tmp_facts:
                #display.vvv("process_db_list(), tmp_facts: %s" % (tmp_facts))
                facts.append(tmp_facts)


        #display.vvv("process_db_list(), result: %s, facts: %s" % (result, facts))
        return result, facts

    # Form sonic-cfggen command, fetch data from running config
    def process_db_table(self, table):
        result = dict()
        cmd = 'sonic-cfggen -d --var-json ' + table
        cmd_mode = cmn.get_command_mode(self.facts_inst._module)
        response = run_commands(self.facts_inst._module, mode=cmd_mode, commands=cmd)

        # Run commands returns list, so extract the result alone
        if not response:
            pass
        else:
            result = response[0]

        #display.vvv("process_db_table(), response: %s, result: %s" % (response, result))
        return result

    # Extract specific entry based on key and return
    def process_db_key(self, entries, key):
        result = None
        if key in entries:
            result = entries[key]

        return result

    # Extract specific entry based on key and return
    def process_db_field(self, entry, field):
        result = None
        if field in entry:
            result = {cmn.DB_VAL_NAME: entry[field]}

        return result

    def generate_facts(self, node, db_data):
        result = dict()
        facts = dict()
        table_name = None
        table_content = None
        #display.vvv("generate_facts(), node : %s, db_data : %s" % (node, db_data))

        # Iterate over all elements in dict
        for k,v in node.items():
            tmp_result = dict()
            #display.vvv("generate_facts(), k : %s, v : %s" % (k, v))

            # Skip the node if not dict
            if not isinstance(v, dict):
                result.update({k: v})
                if not cmn.is_meta_attr(k):
                    facts.update({k: v})
                continue

            # Extract db specific attributes
            db_table = v.get(cmn.DB_TABLE_NAME)
            db_key = v.get(cmn.DB_KEY_NAME)
            db_field = v.get(cmn.DB_FIELD_NAME)
            obj_type = v.get(cmn.TYPE_NAME)
            #display.vvv("generate_facts(), db_table : %s, db_key : %s, db_field : %s, obj_type: %s" % (db_table, db_key, db_field, obj_type))

            # Process nodes recursively
            if not db_table and not db_key and not db_field and not obj_type:
                tmp_result, tmp_facts = self.generate_facts(v, db_data)
                facts.update({k: tmp_facts})
                result.update({k: tmp_result})
                continue

            # Process list
            if obj_type and obj_type == cmn.LIST_NAME:
                if db_table:
                    db_entries = self.process_db_table(db_table)
                # Return when table is empty
                if not db_entries:
                    #display.vvv("Table %s is empty" % (db_table))
                    continue
                tmp_result, tmp_facts = self.process_db_list(v, db_entries)

                cmn.copy_meta_attrs(v, tmp_result)
                facts.update({k: tmp_facts})
                result.update({k: tmp_result})
                continue

            cmn.copy_meta_attrs(v, tmp_result)

            # Process db_table
            if db_table:
                db_entries = self.process_db_table(db_table)
                #display.vvv("generate_facts(), db_entries: %s" % (db_entries))
                # Return when table is empty
                if not db_entries:
                    return result, facts
                # Process db_key when both db_table and db_key are mentioned
                if db_key:

                    db_entry = self.process_db_key(db_entries, db_key)
                    #display.vvv("generate_facts(), db_entry: %s" % (db_entry))
                    # Contine when db_entry is empty
                    if not db_entry:
                        continue

                    tmp_result, tmp_facts = self.generate_facts(v, db_entry)
                    cmn.copy_meta_attrs(v, tmp_result)
                    result.update({k: tmp_result})
                    facts.update({k: tmp_facts})
                    continue

                else:
                    tmp_result, tmp_facts = self.generate_facts(v, db_entries)
                    cmn.copy_meta_attrs(v, tmp_result)
                    result.update({k: tmp_result})
                    facts.update({k: tmp_facts})
                    continue

            # Process db_key
            if db_key:
                # Continue when db_data (records) is empty
                if not db_data:
                    continue

                db_entry = self.process_db_key(db_data, db_key)
                #display.vvv("generate_facts(), db_entry: %s" % (db_entry))
                # Contine when db_entry is empty
                if not db_entry:
                    continue

                # Process db_field when db_key and db_field are both mentioned
                if db_field:
                    db_val = self.process_db_field(db_entry, db_field)
                    #display.vvv("generate_facts(), db_val: %s" % (db_val))
                    if not db_val:
                        continue

                    # Process db_translate_method
                    db_val_translated = None
                    if cmn.DB_TRANSLATE_METHOD_NAME in v:
                        db_translate_method_name = v[cmn.DB_TRANSLATE_METHOD_NAME]
                        db_val_translated = self.process_db_translate_method(db_val, db_translate_method_name)
                        tmp_result.update(db_val_translated)
                    tmp_result.update(db_val)
                    cmn.copy_meta_attrs(v, tmp_result)
                    if db_val_translated:
                        facts.update({k: db_val_translated[cmn.DB_VAL_TRANSLATED_NAME]})
                    else:
                        facts.update({k: db_val[cmn.DB_VAL_NAME]})
                    result.update({k: tmp_result})
                    continue

                tmp_result, tmp_facts = self.generate_facts(v, db_entry)
                cmn.copy_meta_attrs(v, tmp_result)
                result.update({k: tmp_result})
                facts.update({k: tmp_facts})
                continue

            # Process db_field
            if db_field:
                db_val = self.process_db_field(db_data, db_field)
                #display.vvv("generate_facts(), db_val: %s" % (db_val))
                # Continue when db_val is empty
                if not db_val:
                    continue

                db_val_translated = None
                if cmn.DB_TRANSLATE_METHOD_NAME in v:
                    db_translate_method_name = v[cmn.DB_TRANSLATE_METHOD_NAME]
                    db_val_translated = self.process_db_translate_method(db_val, db_translate_method_name)

                tmp_result.update(db_val)
                cmn.copy_meta_attrs(v, tmp_result)
                if db_val_translated:
                    tmp_result.update(db_val_translated)

                if db_val_translated:
                    facts.update({k: db_val_translated[cmn.DB_VAL_TRANSLATED_NAME]})
                else:
                    facts.update({k: db_val[cmn.DB_VAL_NAME]})
                result.update({k: tmp_result})

        #display.vvv("generate_facts(), result : %s" % (result))
        return (result, facts)

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        result = None
        config = deepcopy(conf)
        result = remove_empties(config)
        display.vvv("render_config(), result: %s" % (result))
        return result

